from rest_framework import permissions
from apps.accounts.models import UserRole

class IsCompanyRecruiterOrReadOnly(permissions.BasePermission):
    """
    Allow anyone to view company info, but only the owner recruiter or admin can edit/delete.
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
        return obj.recruiter == request.user

