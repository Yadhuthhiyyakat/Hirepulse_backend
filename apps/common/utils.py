import os
from django.core.exceptions import ValidationError
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

ALLOWED_RESUME_EXTENSIONS = ['.pdf', '.doc', '.docx']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']


def api_response(success=True, data=None, message="Request successful", status_code=status.HTTP_200_OK):
    """
    Standardizes successful responses across non-paginated or custom endpoints.
    Format:
    {
        "success": true,
        "data": {},
        "message": "..."
    }
    """
    payload = {
        'success': success,
        'message': message,
        'data': data if data is not None else {}
    }
    return Response(payload, status=status_code)

def validate_file_extension(file, allowed_extensions):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(allowed_extensions)}")

def validate_file_size(file, max_bytes=None):
    max_size = max_bytes or getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
    if file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError(f"File size exceeds maximum limit of {max_mb:.1f} MB.")

def resume_upload_path(instance, filename):
    return f"resumes/{instance.candidate_id}/{filename}"

def profile_picture_upload_path(instance, filename):
    return f"profiles/{instance.id}/{filename}"

def company_logo_upload_path(instance, filename):
    return f"companies/{instance.id}/{filename}"
