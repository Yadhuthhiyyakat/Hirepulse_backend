from rest_framework import permissions
from .models import UserRole

class IsJobSeeker(permissions.BasePermission):
    """Allows access only to Job Seekers."""
    message = "Access restricted to Job Seekers only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.JOB_SEEKER
        )

class IsRecruiter(permissions.BasePermission):
    """Allows access only to Recruiters."""
    message = "Access restricted to Recruiters only."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.RECRUITER
        )

class IsAdminUser(permissions.BasePermission):
    """Allows access only to Admins."""
    message = "Access restricted to Platform Administrators."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == UserRole.ADMIN or request.user.is_staff or request.user.is_superuser)
        )

class IsSelfOrAdmin(permissions.BasePermission):
    """Allows access to the user themselves or an admin."""
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == UserRole.ADMIN or request.user.is_staff:
            return True
        user = getattr(obj, 'user', obj)
        return user == request.user

