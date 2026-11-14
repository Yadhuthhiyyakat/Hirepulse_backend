from rest_framework import permissions
from apps.accounts.models import UserRole

class IsJobRecruiterOrReadOnly(permissions.BasePermission):
    """
    Allow safe methods for all.
    Allow mutations only for the recruiter who owns the job's company or an admin.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == UserRole.ADMIN or request.user.is_staff:
            return True
        return obj.company.recruiter == request.user

