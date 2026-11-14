from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count, Q

from .models import Job, SavedJob, JobStatus
from .serializers import JobSerializer, JobCreateUpdateSerializer, SavedJobSerializer
from .filters import JobFilter
from .permissions import IsJobRecruiterOrReadOnly
from apps.accounts.models import UserRole
from apps.common.utils import api_response

class JobViewSet(viewsets.ModelViewSet):
    permission_classes = (IsJobRecruiterOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = JobFilter
    ordering_fields = ('created_at', 'salary_min', 'salary_max', 'title', 'application_deadline')
    ordering = ('-created_at',)

    def get_queryset(self):
        user = self.request.user
        queryset = Job.objects.all().select_related(
            'company', 'company__recruiter'
        ).prefetch_related(
            'saved_by_users', 'applications'
        ).annotate(
            active_applications_count=Count('applications', distinct=True)
        )

        # If user is admin, they can see all jobs
        if user and user.is_authenticated and (user.role == UserRole.ADMIN or user.is_staff):
            return queryset

        # For public list/retrieve actions, only show PUBLISHED jobs
        # unless it is the recruiter's own company jobs
        if self.action in ['my_jobs']:
            if user and user.is_authenticated:
                return queryset.filter(company__recruiter=user)
            return queryset.none()

        if user and user.is_authenticated and user.role == UserRole.RECRUITER:
            # Allow recruiters to see published jobs plus their own draft/closed jobs
            return queryset.filter(Q(status=JobStatus.PUBLISHED) | Q(company__recruiter=user))

        return queryset.filter(status=JobStatus.PUBLISHED)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return JobCreateUpdateSerializer
        return JobSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(
            success=True,
            data=serializer.data,
            message="Job details retrieved successfully"
        )

    def create(self, request, *args, **kwargs):
        if request.user.role not in [UserRole.RECRUITER, UserRole.ADMIN]:
            return api_response(
                success=False,
                message="Only recruiters and admins can create job postings.",
                status_code=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        return api_response(
            success=True,
            data=JobSerializer(job, context={'request': request}).data,
            message="Job posted successfully",
            status_code=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        return api_response(
            success=True,
            data=JobSerializer(job, context={'request': request}).data,
            message="Job updated successfully"
        )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def save(self, request, pk=None):
        job = self.get_object()
        saved_instance = SavedJob.objects.filter(user=request.user, job=job).first()

        if saved_instance:
            saved_instance.delete()
            return api_response(
                success=True,
                data={'is_saved': False},
                message="Job removed from saved jobs"
            )
        else:
            SavedJob.objects.create(user=request.user, job=job)
            return api_response(
                success=True,
                data={'is_saved': True},
                message="Job saved successfully"
            )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_jobs(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = JobSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = JobSerializer(queryset, many=True, context={'request': request})
        return api_response(
            success=True,
            data=serializer.data,
            message="Recruiter jobs retrieved"
        )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def saved(self, request):
        saved_jobs = SavedJob.objects.filter(user=request.user).select_related('job', 'job__company').order_by('-created_at')
        page = self.paginate_queryset(saved_jobs)
        if page is not None:
            serializer = SavedJobSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = SavedJobSerializer(saved_jobs, many=True, context={'request': request})
        return api_response(
            success=True,
            data=serializer.data,
            message="Saved jobs retrieved"
        )

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    @transaction.atomic
    def toggle_publish(self, request, pk=None):
        job = self.get_object()
        job = Job.objects.select_for_update().get(pk=job.pk)
        new_status = JobStatus.PUBLISHED if job.status != JobStatus.PUBLISHED else JobStatus.CLOSED
        job.status = new_status
        job.save()
        return api_response(
            success=True,
            data=JobSerializer(job, context={'request': request}).data,
            message=f"Job status changed to {new_status}"
        )

