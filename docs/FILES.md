# Project Structure & File Guide

```text
MiniProject/
├── backend/
│   ├── config/                 # Django settings, URLs, WSGI
│   ├── loans/                  # Django app: models, views, admin, migrations, agents, tools
│   │   ├── agents/             # LangGraph state graph and prompt configuration
│   │   └── tools/              # Separated domain tools (KYC, credit, FOIR, PDF, etc.)
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/                    # React UI and Django API helper
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── docs/                       # Architecture, data flow, and this guide
└── README.md
```

## Backend files

- `backend/loans/agents/graph.py`: LangGraph StateGraph, provider setup, and tool execution loop.
- `backend/loans/tools/`: Dedicated Python modules for each domain tool:
  - `update_profile.py`: saves applicant personal and income details.
  - `verify_kyc.py`: validates 12-digit Aadhaar and DOB against database records.
  - `credit_score.py`: looks up credit score and existing EMIs via PAN.
  - `calculate_foir.py`: computes Fixed Obligation to Income Ratio and assigns risk.
  - `available_loans.py`: lists configured loan products from the database.
  - `generate_loan_pdf.py`: creates the loan sanction PDF using ReportLab.
  - `utils.py`: string-to-numeric amount parser ('50k', '1.5m', etc.).
- `backend/loans/views.py`: signup, login, current-user, logout, chat, and OCR endpoints.
- `backend/loans/models.py`: user, loan product, KYC record, credit record, and chat session models.
- `backend/loans/admin.py`: admin registration for managing products and verification records.
- `backend/loans/migrations/`: versioned database schema.
- `backend/config/settings.py`: app configuration, SQLite default, CORS, media, and authentication.

## Frontend files

- `frontend/src/main.tsx`: mounts the React application.
- `frontend/src/app/react-home.tsx`: chat, document upload, stage indicator, and PDF link.
- `frontend/src/components/react-login-signup.tsx`: authentication forms.
- `frontend/src/api.ts`: Django API base URL, cookies, and CSRF header.
- `frontend/vite.config.ts`: React and Tailwind Vite plugins.

