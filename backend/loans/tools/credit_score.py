import re
from langchain_core.tools import tool
from ..models import CreditRecord
from ..crypto import hash_identity, mask_pan

def create_credit_score_tool(get_session):
    @tool
    def getCreditScore(pan: str) -> dict:
        """Look up the applicant's credit score and existing EMI using their PAN, after KYC succeeds."""
        session = get_session()
        if session.stage != "credit" or not session.state.get("kycResult", {}).get("verified"):
            return {"success": False, "creditScoreLow": True, "message": "KYC must be verified before checking credit."}

        normalized_pan = re.sub(r"\s", "", pan).upper()
        
        # P2: Search by deterministic HMAC-SHA256 hash (never search or store plaintext PAN)
        p_hash = hash_identity(normalized_pan)
        record = CreditRecord.objects.filter(pan_hash=p_hash).first()

        # Automatic upgrade for unmigrated legacy records
        if not record:
            legacy_record = CreditRecord.objects.filter(pan__iexact=normalized_pan).first()
            if legacy_record:
                legacy_record.set_pan(normalized_pan)
                legacy_record.save(update_fields=["pan_hash", "encrypted_pan", "pan"])
                record = legacy_record

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
        # P2: Retain only the masked PAN in session state
        session.state["creditLookup"] = {
            "score": record.score,
            "scoreCategory": category,
            "emi": float(record.emi),
            "maskedPan": mask_pan(normalized_pan),
        }
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
