# Loan Assistant

Loan Assistant is now split into a Django REST backend and a React/Vite frontend. The existing loan assistant interface is retained, while Django handles accounts, application sessions, KYC and credit lookups, and document OCR.

## Prerequisites

- Python 3.11 or newer (Python 3.11–3.13 avoids the current LangChain compatibility warning on Python 3.14)
- Node.js 20 or newer
- A Google Gemini API key for the LangGraph assistant and document OCR

## Start the backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Set `GEMINI_API_KEY` (or `LLM_API_KEY`), `LLM_BASE_URL`, and `LLM_MODEL` in `backend/.env` for the LangGraph assistant and OCR. The default model is `gemini-2.5-flash`. The API listens on `http://localhost:8000`; manage loan products and verification records at `/admin/`.


## Start the frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and calls the Django API at `http://localhost:8000`. Set `VITE_API_BASE_URL` in `frontend/.env` to change the API origin.

## Migrating existing data

The old application stored users, loans, KYC records, and credit records in MongoDB. The Django backend uses SQLite by default and defines corresponding relational models. Existing MongoDB records are not copied automatically: export/import the collections into Django before switching users to the new backend. Create loan, KYC, and credit records through Django admin or import fixtures. Configure `DJANGO_SECRET_KEY`, allowed hosts, and HTTPS cookie/security settings before deployment.

## Current API

- `POST /api/auth/signup/`, `POST /api/auth/login/`, `GET /api/auth/me/`, `POST /api/auth/logout/`
- `POST /api/chat/` for the LangGraph loan assistant
- `POST /api/ocr/upload/` for image extraction

The chat lifecycle is implemented as a LangGraph `StateGraph` with Django-backed tools for profile updates, KYC, credit and FOIR checks, product lookup, and PDF generation.
