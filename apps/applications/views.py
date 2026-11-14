from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Application, ApplicationStatus
from .serializers import (
    ApplicationSerializer,
    ApplicationCreateSerializer,
    ApplicationStatusUpdateSerializer
)
from .permissions import IsApplicationParticipantOrAdmin
from apps.accounts.models import User, UserRole
from apps.companies.models import Company
from apps.jobs.models import Job, SavedJob, JobStatus
from apps.notifications.services import create_notification
from apps.common.utils import api_response

class ApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsApplicationParticipantOrAdmin)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ('status', 'job')
    search_fields = ('candidate__first_name', 'candidate__last_name', 'candidate__email', 'job__title')
    ordering_fields = ('applied_at', 'status')
    ordering = ('-applied_at',)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Application.objects.none()

        if user.role == UserRole.ADMIN or user.is_staff:
            return Application.objects.all().select_related('job', 'candidate', 'candidate__profile', 'job__company')

        if user.role == UserRole.RECRUITER:
            return Application.objects.filter(
                job__company__recruiter=user
            ).select_related('job', 'candidate', 'candidate__profile', 'job__company')

        # Job Seeker: their own applications
        return Application.objects.filter(
            candidate=user
        ).select_related('job', 'candidate', 'candidate__profile', 'job__company')

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        if self.action in ['update_status', 'partial_update', 'update']:
            return ApplicationStatusUpdateSerializer
        return ApplicationSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(
            success=True,
            data=serializer.data,
            message="Application details retrieved successfully"
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if request.user.role != UserRole.JOB_SEEKER:
            return api_response(
                success=False,
                message="Only job seekers can apply for jobs.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        # Send notification to the recruiter of this job on successful commit
        def send_recruiter_notification():
            try:
                recruiter = getattr(getattr(application.job, 'company', None), 'recruiter', None)
                if recruiter:
                    create_notification(
                        user=recruiter,
                        title="New Application Received",
                        message=f"{request.user.full_name} applied for your job '{application.job.title}'.",
                        notification_type='NEW_APPLICATION',
                        data={'application_id': str(application.id), 'job_id': str(application.job.id)}
                    )
            except Exception:
                pass

        transaction.on_commit(send_recruiter_notification)

        return api_response(
            success=True,
            data=ApplicationSerializer(application, context={'request': request}).data,
            message="Application submitted successfully",
            status_code=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    @transaction.atomic
    def update_status(self, request, pk=None):
        application = self.get_object()
        if request.user.role not in [UserRole.RECRUITER, UserRole.ADMIN]:
            return api_response(
                success=False,
                message="Only recruiters and admins can update application status.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = ApplicationStatusUpdateSerializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return api_response(
            success=True,
            data=ApplicationSerializer(application, context={'request': request}).data,
            message=f"Application status updated to {application.get_status_display()}"
        )

    @action(detail=False, methods=['get'])
    def jobseeker_stats(self, request):
        user = request.user
        app_stats = Application.objects.filter(candidate=user).aggregate(
            total_apps=Count('id'),
            interviews=Count('id', filter=Q(status=ApplicationStatus.INTERVIEW))
        )
        saved_jobs = SavedJob.objects.filter(user=user).count()

        # Calculate profile completion percentage
        profile = getattr(user, 'profile', None)
        completion = 30  # Base for having an account
        if user.first_name and user.last_name:
            completion += 10
        if user.phone:
            completion += 10
        if profile:
            if profile.bio:
                completion += 10
            if profile.location:
                completion += 10
            if profile.skills and len(profile.skills) > 0:
                completion += 15
            if profile.resume:
                completion += 15

        stats = {
            'total_applications': app_stats['total_apps'] or 0,
            'saved_jobs': saved_jobs,
            'interviews': app_stats['interviews'] or 0,
            'profile_completion': min(completion, 100)
        }
        return api_response(success=True, data=stats, message="Job seeker stats retrieved")

    @action(detail=False, methods=['get'])
    def recruiter_stats(self, request):
        user = request.user
        if user.role not in [UserRole.RECRUITER, UserRole.ADMIN]:
            return api_response(success=False, message="Forbidden", status_code=status.HTTP_403_FORBIDDEN)

        active_jobs = Job.objects.filter(company__recruiter=user, status=JobStatus.PUBLISHED).count()
        apps_stats = Application.objects.filter(job__company__recruiter=user).aggregate(
            total_apps=Count('id'),
            shortlisted=Count('id', filter=Q(status=ApplicationStatus.SHORTLISTED)),
            interviews=Count('id', filter=Q(status=ApplicationStatus.INTERVIEW)),
            hired=Count('id', filter=Q(status=ApplicationStatus.HIRED)),
        )

        stats = {
            'active_jobs': active_jobs,
            'total_applications': apps_stats['total_apps'] or 0,
            'shortlisted': apps_stats['shortlisted'] or 0,
            'interviews': apps_stats['interviews'] or 0,
            'hired': apps_stats['hired'] or 0
        }
        return api_response(success=True, data=stats, message="Recruiter stats retrieved")

    @action(detail=False, methods=['get'])
    def admin_stats(self, request):
        user = request.user
        if not (user.role == UserRole.ADMIN or user.is_staff):
            return api_response(success=False, message="Forbidden", status_code=status.HTTP_403_FORBIDDEN)

        total_users = User.objects.count()
        total_companies = Company.objects.count()
        total_jobs = Job.objects.count()
        total_applications = Application.objects.count()

        users_by_role = list(User.objects.values('role').annotate(count=Count('id')))
        jobs_by_type = list(Job.objects.values('job_type').annotate(count=Count('id')))
        applications_by_status = list(Application.objects.values('status').annotate(count=Count('id')))

        # Monthly trends (last 6 months)
        now = timezone.now()
        trends = []
        for i in range(5, -1, -1):
            start_month = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
            end_month = (start_month + timedelta(days=32)).replace(day=1)
            month_label = start_month.strftime('%b %Y')
            jobs_c = Job.objects.filter(created_at__gte=start_month, created_at__lt=end_month).count()
            apps_c = Application.objects.filter(applied_at__gte=start_month, applied_at__lt=end_month).count()
            trends.append({
                'month': month_label,
                'jobs': jobs_c,
                'applications': apps_c
            })

        stats = {
            'total_users': total_users,
            'total_companies': total_companies,
            'total_jobs': total_jobs,
            'total_applications': total_applications,
            'users_by_role': users_by_role,
            'jobs_by_type': jobs_by_type,
            'applications_by_status': applications_by_status,
            'trends': trends
        }
        return api_response(success=True, data=stats, message="Admin platform statistics retrieved")

