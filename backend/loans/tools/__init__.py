from .update_profile import create_update_profile_tool
from .verify_kyc import create_verify_kyc_tool
from .credit_score import create_credit_score_tool
from .calculate_foir import create_calculate_foir_tool
from .available_loans import create_available_loans_tool
from .generate_loan_pdf import create_generate_loan_pdf_tool

def build_tools(session_id: str, user_id: int):
    """Factory that builds the 6 session-bound domain tools for the applicant."""
    from ..models import ChatSession

    def get_session():
        return ChatSession.objects.get(session_id=session_id, user_id=user_id)

    return [
        create_update_profile_tool(get_session),
        create_verify_kyc_tool(get_session),
        create_credit_score_tool(get_session),
        create_calculate_foir_tool(get_session),
        create_available_loans_tool(get_session),
        create_generate_loan_pdf_tool(get_session),
    ]

__all__ = ["build_tools"]
