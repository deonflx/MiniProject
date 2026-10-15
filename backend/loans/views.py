import logging
import json, os, re
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from .models import ChatSession, Loan

User = get_user_model()
logger = logging.getLogger(__name__)

def _safe_provider_error(exc):
    detail = str(exc)
    for name in ("GEMINI_API_KEY", "LLM_API_KEY", "CEREBRAS_API_KEY", "GROQ_API_KEY"):
        secret = os.getenv(name)
        if secret:
            detail = detail.replace(secret, "[redacted]")
    return f"{type(exc).__name__}: {detail}"[:500]


def body(request):
    try: return json.loads(request.body or "{}")
    except json.JSONDecodeError: return {}

@require_POST
@csrf_protect
def signup(request):
    data = body(request); name = str(data.get("name", "")).strip(); email = str(data.get("email", "")).strip().lower(); password = data.get("password", "")
    if not name or not email or len(password) < 8: return JsonResponse({"error": "Name, email, and a password of at least 8 characters are required."}, status=400)
    if User.objects.filter(email=email).exists(): return JsonResponse({"error": "User already exists"}, status=400)
    user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
    auth_login(request, user)
    return JsonResponse({"success": True, "user": {"name": name, "email": email}})

@require_POST
@csrf_protect
def login(request):
    data = body(request); user = authenticate(request, username=str(data.get("email", "")).lower(), password=data.get("password", ""))
    if user is None: return JsonResponse({"error": "Invalid credentials"}, status=400)
    auth_login(request, user)
    return JsonResponse({"success": True, "user": {"name": user.first_name or user.username, "email": user.email}})

@require_GET
@ensure_csrf_cookie
def me(request):
    if not request.user.is_authenticated: return JsonResponse({"authenticated": False}, status=401)
    return JsonResponse({"authenticated": True, "user": {"name": request.user.first_name or request.user.username, "email": request.user.email}})

@require_POST
def logout(request):
    auth_logout(request); return JsonResponse({"success": True})

@require_POST
@login_required
@csrf_protect
def chat(request):
    data = body(request); session_id = str(data.get("sessionId", "")); message = str(data.get("message", "")).strip()
    if not session_id or not message: return JsonResponse({"error": "sessionId and message are required"}, status=400)
    session = ChatSession.objects.filter(session_id=session_id, user=request.user).first()
    if not session:
        if ChatSession.objects.filter(session_id=session_id).exists(): return JsonResponse({"error": "Session not found"}, status=404)
        session = ChatSession.objects.create(session_id=session_id, user=request.user)
    affirmative = bool(re.search(r"\b(yes|yeah|yep|sure|show|please|proceed|okay|ok)\b", message, re.I))
    if session.state.get("creditResult", {}).get("eligible") and session.stage == "credit" and affirmative:
        session.state["loanOptionsRequested"] = True
    if session.stage == "loan_selection" and session.state.get("availableLoans"):
        available = Loan.objects.filter(external_id__in=session.state["availableLoans"])
        selected = next((loan for loan in available if loan.name.casefold() in message.casefold()), None)
        if selected:
            session.state["selectedLoanRequest"] = selected.name
    safe_message = message
    if session.stage == "kyc": safe_message = re.sub(r"(?<!\d)(?:\d[\s-]?){11}\d(?!\d)", "[REDACTED Aadhaar]", message)
    if session.stage == "credit": safe_message = re.sub(r"\b[A-Z]{5}\d{4}[A-Z]\b", "[REDACTED PAN]", message, flags=re.I)
    session.logs = (session.logs + [{"role": "user", "content": safe_message}])[-8:]
    session.save(update_fields=["logs", "state"])
    conversation = [{"role": item["role"], "content": item["content"]} for item in session.logs[:-1]]
    conversation.append({"role": "user", "content": message})
    try:
        from .agents.graph import reply_for
        reply = reply_for(session.session_id, request.user.id, conversation)
    except RuntimeError as exc:
        return JsonResponse({"error": str(exc)}, status=503)
    except Exception as exc:
        safe_error = _safe_provider_error(exc)
        logger.error("LangGraph request failed for session %s: %s", session_id, safe_error)
        error = f"Assistant provider error ({safe_error})" if settings.DEBUG else "The assistant could not process this message. Check the LLM provider configuration and try again."
        return JsonResponse({"error": error}, status=502)
    session.refresh_from_db()
    session.logs = (session.logs + [{"role": "assistant", "content": reply}])[-8:]
    session.save(update_fields=["logs"])
    return JsonResponse({"response": reply, "session": {"sessionId": session.session_id, "stage": session.stage, "profile": session.profile, **session.state}, **session.state})

@require_POST
@login_required
@csrf_protect
def ocr_upload(request):
    file = request.FILES.get("file")
    if not file: return JsonResponse({"error": "No file uploaded"}, status=400)
    if file.size > 8 * 1024 * 1024: return JsonResponse({"error": "File must be smaller than 8 MB"}, status=400)
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}: return JsonResponse({"error": "Upload a JPEG, PNG, or WebP image"}, status=400)
    key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")
    if not key: return JsonResponse({"error": "OCR is not configured. Add GEMINI_API_KEY to backend/.env."}, status=503)
    base_url = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/").rstrip("/")
    endpoint = f"{base_url}/chat/completions"
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    import base64, requests
    image = base64.b64encode(file.read()).decode()
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract name, job title and salary from salary slips; name, Aadhaar number and date of birth (YYYY-MM-DD) from Aadhaar cards; name and PAN from PAN cards. Return only labeled extracted fields."},
                    {"type": "image_url", "image_url": {"url": f"data:{file.content_type};base64,{image}"}}
                ]
            }
        ]
    }
    try:
        result = requests.post(endpoint, headers={"Authorization": f"Bearer {key}"}, json=payload, timeout=60)
        result.raise_for_status()
        text = result.json()["choices"][0]["message"]["content"]
        return JsonResponse({"text": text})
    except Exception as exc: return JsonResponse({"error": f"OCR failed: {exc}"}, status=502)

