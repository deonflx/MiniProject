import base64
import logging
import os
import jwt
from jwt import PyJWKClient
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
_jwk_client = None

def get_jwks_url():
    """Derive Clerk JWKS URL from environment variables."""
    jwks_url = os.getenv("CLERK_JWKS_URL")
    if jwks_url:
        return jwks_url

    frontend_api = os.getenv("CLERK_FRONTEND_API")
    if frontend_api:
        return f"https://{frontend_api.strip('/')}/.well-known/jwks.json"

    pk = os.getenv("CLERK_PUBLISHABLE_KEY")
    if pk and pk.startswith("pk_"):
        try:
            parts = pk.split("_")
            raw = parts[2] if len(parts) > 2 else parts[1]
            padded = raw + "=" * (-len(raw) % 4)
            decoded = base64.b64decode(padded).decode("utf-8").rstrip("$")
            return f"https://{decoded}/.well-known/jwks.json"
        except Exception as e:
            logger.warning(f"Could not parse CLERK_PUBLISHABLE_KEY for JWKS URL: {e}")

    return None

def verify_clerk_token(token: str):
    """
    Verifies a Clerk session JWT and returns the claims dict.
    Returns None if verification fails.
    """
    global _jwk_client
    if not token:
        return None

    # 1. Verification via PEM public key if provided in .env
    pem_key = os.getenv("CLERK_PEM_PUBLIC_KEY")
    if pem_key:
        try:
            formatted_key = pem_key.replace("\\n", "\n")
            if not formatted_key.strip().startswith("-----BEGIN"):
                formatted_key = f"-----BEGIN PUBLIC KEY-----\n{formatted_key.strip()}\n-----END PUBLIC KEY-----"
            return jwt.decode(token, formatted_key, algorithms=["RS256"], options={"verify_exp": True})
        except Exception as e:
            logger.warning(f"Clerk PEM verification failed: {e}")

    # 2. Verification via Clerk's JWKS endpoint
    jwks_url = get_jwks_url()
    if jwks_url:
        try:
            if _jwk_client is None:
                _jwk_client = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)
            signing_key = _jwk_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_exp": True}
            )
        except Exception as e:
            logger.warning(f"Clerk JWKS verification failed: {e}")

    # 3. Development fallback when DEBUG=True and external key servers are not reachable
    if os.getenv("DJANGO_DEBUG", "false").lower() == "true":
        try:
            logger.warning("Falling back to unverified JWT decode in DEBUG mode.")
            return jwt.decode(token, options={"verify_signature": False, "verify_exp": True})
        except Exception as e:
            logger.error(f"Unverified JWT decode failed: {e}")

    return None

def get_or_create_clerk_user(claims: dict):
    """
    Resolves or provisions a Django User for the verified Clerk user claims.
    """
    if not claims:
        return None

    User = get_user_model()
    clerk_id = claims.get("sub")
    if not clerk_id:
        return None

    email = claims.get("email") or claims.get("email_address") or f"{clerk_id}@clerk.user"
    first_name = claims.get("first_name") or claims.get("name") or clerk_id

    # 1. Try finding by username (clerk_id)
    user = User.objects.filter(username=clerk_id).first()
    if user:
        return user

    # 2. Try finding by email
    user = User.objects.filter(email=email).first()
    if user:
        return user

    # 3. Create a new user record
    try:
        user = User.objects.create_user(
            username=clerk_id,
            email=email,
            first_name=first_name,
        )
        return user
    except Exception as e:
        logger.error(f"Failed to create user for Clerk ID {clerk_id}: {e}")
        return None
