from rest_framework import permissions
from apps.accounts.models import UserRole

class IsApplicationParticipantOrAdmin(permissions.BasePermission):
    """
    Allow candidate, recruiter of the job's company, or admin.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == UserRole.ADMIN or request.user.is_staff:
            return True
        # Candidate can read their application
        if obj.candidate == request.user:
            return request.method in permissions.SAFE_METHODS
        # Recruiter of company can read and update
        if obj.job.company.recruiter == request.user:
            return True
        return False

