from langchain_core.tools import tool
from .utils import parse_amount

def create_update_profile_tool(get_session):
    @tool
    def updateProfile(
        name: str | None = None,
        income: str | float | None = None,
        employment: str | None = None,
        existing_emi: str | float | None = None
    ) -> dict:
        """Save applicant name, monthly income, employment type, or current EMI when supplied by the applicant or document OCR."""
        session = get_session()
        for field, value in (
            ("name", name),
            ("income", parse_amount(income)),
            ("employment", employment),
            ("existing_emi", parse_amount(existing_emi)),
        ):
            if value is not None and value != "":
                session.profile[field] = value.strip() if isinstance(value, str) else value

        if all(session.profile.get(field) for field in ("name", "income", "employment")) and session.stage == "sales":
            session.stage = "kyc"

        session.save(update_fields=["profile", "stage"])
        return {"profile": session.profile, "stage": session.stage, "message": "Applicant profile updated."}

    return updateProfile
