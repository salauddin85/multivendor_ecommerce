from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, Throttled
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError, AuthenticationFailed


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, NotAuthenticated):
        return Response({
            "code": 401,
            "status": "failed",
            "message": "Authentication credentials were not provided.",
            "errors": {
                "request": ["Invalid request"]
            },
        }, status=status.HTTP_401_UNAUTHORIZED)

    elif isinstance(exc, PermissionDenied):
        return Response({
            "code": 403,
            "status": "failed",
            "message": "You do not have permission to perform this action.",
            "errors": {
                "request": ["Invalid request"]
            },

        }, status=status.HTTP_403_FORBIDDEN)

    # Handle invalid or expired tokens
    elif isinstance(exc, (InvalidToken, TokenError, AuthenticationFailed)):
        return Response({
            "code": 401,
            "status": "failed",
            "message": "Token is invalid or expired.",
            "errors": {
                "token": ["Token is invalid or expired"]
            }
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Handle Throttling Errors (Rate Limiting)
    elif isinstance(exc, Throttled):
        return Response({
            "code": 429,
            "status": "failed",
            "message": "Too many requests. Please try again later.",
            "errors": {
                "request": ["Rate limit exceeded"]
            },
            "retry_after": exc.wait  # Include the wait time before retrying
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)

    return response
