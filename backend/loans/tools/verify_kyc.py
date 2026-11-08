import re
from datetime import date
from langchain_core.tools import tool
from ..models import KYCRecord
from ..crypto import hash_identity, mask_aadhaar

def create_verify_kyc_tool(get_session):
    @tool
    def verifyKYC(aadhar_no: str, dob: str) -> dict:
        """Verify the applicant's 12-digit Aadhaar number and date of birth against KYC records. Do not call until both were provided."""
        session = get_session()
        if session.stage != "kyc" or not all(session.profile.get(field) for field in ("name", "income", "employment")):
            return {"success": False, "kycFailed": True, "message": "Complete the applicant profile before KYC."}

        aadhaar = re.sub(r"\D", "", aadhar_no)
        try:
            birth_date = date.fromisoformat(dob.strip())
        except (TypeError, ValueError):
            return {"success": False, "kycFailed": True, "message": "Date of birth must use YYYY-MM-DD format."}

        if len(aadhaar) != 12:
            return {"success": False, "kycFailed": True, "message": "Aadhaar must be a valid 12-digit number."}

        # P0: Query using salted HMAC-SHA256 hash (never query or match against plaintext Aadhaar)
        a_hash = hash_identity(aadhaar)
        record = KYCRecord.objects.filter(aadhaar_hash=a_hash, dob=birth_date).first()

        # Automatic upgrade for unmigrated legacy records
        if not record:
            legacy_record = KYCRecord.objects.filter(aadhaar_no=aadhaar, dob=birth_date).first()
            if legacy_record:
                legacy_record.set_aadhaar(aadhaar)
                legacy_record.save(update_fields=["aadhaar_hash", "aadhaar_last4", "aadhaar_no"])
                record = legacy_record

        if not record:
            session.state["kycResult"] = {"verified": False, "message": "Aadhaar details did not match our records."}
            session.stage = "done"
            session.save(update_fields=["state", "stage"])
            return {"success": False, "kycFailed": True, "message": "KYC verification failed. The Aadhaar details do not match our records."}

        # P0: Retain only the masked Aadhaar in session state
        session.state["kycResult"] = {
            "verified": True,
            "message": "KYC verified successfully.",
            "maskedAadhaar": mask_aadhaar(aadhaar)
        }
        session.stage = "credit"
        session.save(update_fields=["state", "stage"])
        return {"success": True, "kycFailed": False, "message": "KYC verified successfully.", "full_name": record.full_name}

    return verifyKYC
