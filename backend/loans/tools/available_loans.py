from langchain_core.tools import tool
from ..models import Loan

def create_available_loans_tool(get_session):
    @tool
    def getAvailableLoans() -> dict:
        """List configured loan products after the applicant has passed KYC, credit score, and FOIR eligibility."""
        session = get_session()
        if not session.state.get("creditResult", {}).get("eligible") or not session.state.get("loanOptionsRequested"):
            return {"loans": [], "error": "The applicant must be eligible and confirm that they want to see loan options."}

        loans = list(Loan.objects.order_by("name"))
        session.stage = "loan_selection"
        session.state["availableLoans"] = [loan.external_id for loan in loans]
        session.save(update_fields=["stage", "state"])

        return {
            "loans": [
                {
                    "id": loan.external_id,
                    "name": loan.name,
                    "interestRate": float(loan.interest_rate),
                    "maxAmount": float(loan.max_amount),
                    "tenureMonths": loan.tenure_months,
                    "description": loan.description
                }
                for loan in loans
            ]
        }

    return getAvailableLoans
