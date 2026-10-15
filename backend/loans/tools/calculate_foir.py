from langchain_core.tools import tool
from .utils import parse_amount

def create_calculate_foir_tool(get_session):
    @tool
    def calculateFOIR(
        income: str | float | None = None,
        existing_emi: str | float | None = None,
        creditScore: int | None = None
    ) -> dict:
        """Calculate FOIR eligibility using monthly income, monthly EMI obligations, and the verified credit score."""
        session = get_session()
        credit = session.state.get("creditLookup", {})
        if not credit or credit.get("score", 0) < 600:
            return {"foir": 0, "eligible": False, "error": "A qualifying credit score is required."}

        monthly_income = parse_amount(session.profile.get("income")) or parse_amount(income) or 0
        emi = float(credit.get("emi", 0))
        score = int(credit.get("score", creditScore or 0))

        if monthly_income <= 0:
            return {"foir": 0, "eligible": False, "error": "Monthly income must be greater than zero."}

        foir = round(emi / monthly_income * 100, 2)
        eligible = foir <= 50 and score >= 600
        risk = "HIGH" if foir > 40 or score < 650 else "MEDIUM" if foir > 20 or score < 700 else "LOW"

        result = {
            "foir": foir,
            "creditScore": score,
            "risk": risk,
            "eligible": eligible,
            "explanation": (
                f"FOIR is {foir}% and credit score is {score}. " +
                ("You are eligible." if eligible else "FOIR exceeds the 50% limit.")
            )
        }
        session.state["creditResult"] = {key: result[key] for key in ("foir", "risk", "eligible", "explanation")}
        session.stage = "credit" if eligible else "done"
        session.save(update_fields=["state", "stage"])
        return result

    return calculateFOIR
