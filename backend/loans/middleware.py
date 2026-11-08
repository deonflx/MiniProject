import logging
from django.contrib.auth.models import AnonymousUser
from .clerk_auth import verify_clerk_token, get_or_create_clerk_user

logger = logging.getLogger(__name__)

class ClerkAuthMiddleware:
    """
    Middleware that authenticates requests bearing a Clerk Bearer JWT
    in the Authorization header and populates request.user.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ", 1)[1].strip()
            claims = verify_clerk_token(token)
            if claims:
                user = get_or_create_clerk_user(claims)
                if user:
                    request.user = user
                    # Token-based authentication does not require CSRF token validation
                    request._dont_enforce_csrf_checks = True
                else:
                    logger.warning("Clerk token verified but user resolution failed.")
            else:
                logger.warning("Clerk token verification failed.")

        return self.get_response(request)
