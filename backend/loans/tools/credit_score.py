import re
from langchain_core.tools import tool
from ..models import CreditRecord

def create_credit_score_tool(get_session):
    @tool
    def getCreditScore(pan: str) -> dict:
        """Look up the applicant's credit score and existing EMI using their PAN, after KYC succeeds."""
        session = get_session()
        if session.stage != "credit" or not session.state.get("kycResult", {}).get("verified"):
            return {"success": False, "creditScoreLow": True, "message": "KYC must be verified before checking credit."}

        normalized_pan = re.sub(r"\s", "", pan).upper()
        record = CreditRecord.objects.filter(pan__iexact=normalized_pan).first()
        if not record:
            session.stage = "done"
            session.state["creditResult"] = {"eligible": False, "score": None}
            session.save(update_fields=["stage", "state"])
            return {
                "success": False,
                "creditScoreLow": True,
                "scoreCategory": "UNKNOWN",
                "message": "No credit record found. Cannot proceed without a valid credit record."
            }

        category = (
            "EXCELLENT" if record.score >= 750 else
            "GOOD" if record.score >= 700 else
            "FAIR" if record.score >= 650 else
            "POOR" if record.score >= 600 else "VERY LOW"
        )
        low = record.score < 600
        session.state["creditLookup"] = {"score": record.score, "scoreCategory": category, "emi": float(record.emi)}
        if low:
            session.stage = "done"
            session.state["creditResult"] = {"eligible": False, "score": record.score, "scoreCategory": category}

        session.save(update_fields=["stage", "state"])
        return {
            "success": True,
            "creditScoreLow": low,
            "scoreCategory": category,
            "score": record.score,
            "emi": float(record.emi),
            "message": f"Credit score is {record.score} ({category})."
        }

    return getCreditScore
