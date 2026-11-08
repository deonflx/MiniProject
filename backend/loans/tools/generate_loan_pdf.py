import os
import re
import time
from pathlib import Path
from django.conf import settings
from langchain_core.tools import tool
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from ..models import Loan

def purge_expired_pdfs(max_age_seconds: int = 1800):
    """
    P3: Auto-purge routine that deletes generated PDFs older than the retention window
    (default: 30 minutes) to prevent sensitive financial documents from sitting indefinitely on disk.
    """
    pdf_dir = Path(settings.MEDIA_ROOT) / "pdfs"
    if not pdf_dir.exists():
        return
    now = time.time()
    for item in pdf_dir.glob("*.pdf"):
        if item.is_file():
            try:
                if now - item.stat().st_mtime > max_age_seconds:
                    item.unlink(missing_ok=True)
            except Exception:
                pass

def create_generate_loan_pdf_tool(get_session):
    @tool
    def generateLoanPDF(loanName: str) -> dict:
        """Generate a loan confirmation PDF for a loan product returned by getAvailableLoans after the applicant chooses it."""
        session = get_session()
        if (
            session.stage != "loan_selection"
            or not session.state.get("creditResult", {}).get("eligible")
            or session.state.get("selectedLoanRequest") != loanName.strip()
        ):
            return {"success": False, "message": "The applicant must be eligible and have selected a loan option."}

        loan = Loan.objects.filter(name__iexact=loanName.strip()).first()
        if not loan or loan.external_id not in session.state.get("availableLoans", []):
            return {"success": False, "message": "That loan is not in the available products list."}

        # P3: Purge expired loan PDFs before creating a new one
        purge_expired_pdfs(max_age_seconds=1800)

        safe_session_id = re.sub(r"[^a-zA-Z0-9_-]", "_", session.session_id)
        pdf_dir = Path(settings.MEDIA_ROOT) / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        filename = f"loan_{safe_session_id}.pdf"

        pdf = canvas.Canvas(str(pdf_dir / filename), pagesize=letter)
        pdf.setTitle("Loan Confirmation")
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawCentredString(306, 740, "LOAN CONFIRMATION")
        pdf.setFont("Helvetica", 12)

        details = [
            ("Applicant", str(session.profile.get("name", "Applicant"))),
            ("Employment", str(session.profile.get("employment", ""))),
            ("Monthly income", f"INR {float(session.profile.get('income', 0)):,.2f}"),
            ("Loan product", loan.name),
            ("Maximum loan amount", f"INR {float(loan.max_amount):,.2f}"),
            ("Tenure", f"{loan.tenure_months} months"),
            ("Interest rate", f"{float(loan.interest_rate)}% per annum")
        ]

        y = 680
        for label, value in details:
            pdf.drawString(90, y, f"{label}: {value}")
            y -= 28

        rate = float(loan.interest_rate) / 1200
        amount = float(loan.max_amount)
        months = loan.tenure_months
        emi = amount / months if not rate else amount * rate * (1 + rate) ** months / ((1 + rate) ** months - 1)

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(90, y - 10, f"Estimated monthly EMI: INR {emi:,.2f}")
        pdf.setFont("Helvetica", 9)
        pdf.drawCentredString(306, 70, "Computer generated document. Final terms are subject to lender approval.")
        pdf.save()

        path = f"{settings.MEDIA_URL}pdfs/{filename}"
        session.state["selectedLoan"] = {
            "name": loan.name,
            "amount": amount,
            "tenure": months,
            "interestRate": float(loan.interest_rate)
        }
        session.state["pdfPath"] = path
        session.stage = "done"
        session.save(update_fields=["state", "stage"])

        return {
            "success": True,
            "pdfPath": path,
            "message": f"[Download Loan Confirmation PDF]({path})"
        }

    return generateLoanPDF
