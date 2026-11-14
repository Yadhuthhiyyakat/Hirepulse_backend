from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Returns custom JSON error response matching:
    {
      "success": false,
      "message": "...",
      "errors": {}
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        errors = response.data
        message = "An error occurred"

        # Determine user-friendly top-level message
        if isinstance(errors, dict):
            if 'detail' in errors:
                message = str(errors['detail'])
                # If detail is present, we keep errors as the dict or specific fields
            elif 'non_field_errors' in errors:
                message = str(errors['non_field_errors'][0]) if isinstance(errors['non_field_errors'], list) else str(errors['non_field_errors'])
            else:
                message = "Validation failed"
        elif isinstance(errors, list):
            message = str(errors[0]) if errors else "Validation failed"
            errors = {"non_field_errors": errors}

        response.data = {
            'success': False,
            'message': message,
            'errors': errors
        }
        return response

    # Handle unhandled 500 exceptions
    logger.exception("Unhandled Exception: %s", exc)
    from django.conf import settings
    error_detail = [str(exc)] if settings.DEBUG else ['An unexpected internal server error occurred.']
    return Response({
        'success': False,
        'message': 'A server error occurred. Please try again later.',
        'errors': {'server': error_detail}
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

