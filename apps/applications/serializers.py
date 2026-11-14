from rest_framework import serializers
from .models import Application, ApplicationStatus
from apps.jobs.models import Job
from apps.jobs.serializers import JobSerializer
from apps.accounts.serializers import UserSerializer
from apps.accounts.models import UserRole

class ApplicationCandidateSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    bio = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    education = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    portfolio_url = serializers.SerializerMethodField()
    linkedin_url = serializers.SerializerMethodField()
    github_url = serializers.SerializerMethodField()

    class Meta:
        from apps.accounts.models import User
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'profile_picture', 'bio', 'location', 'skills',
            'education', 'experience', 'portfolio_url', 'linkedin_url', 'github_url'
        ]

    def _get_profile(self, obj):
        try:
            return getattr(obj, 'profile', None)
        except Exception:
            return None

    def get_bio(self, obj) -> str:
        p = self._get_profile(obj)
        return p.bio if p else ''

    def get_location(self, obj) -> str:
        p = self._get_profile(obj)
        return p.location if p else ''

    def get_skills(self, obj) -> list:
        p = self._get_profile(obj)
        return p.skills if p else []

    def get_education(self, obj) -> list:
        p = self._get_profile(obj)
        return p.education if p else []

    def get_experience(self, obj) -> list:
        p = self._get_profile(obj)
        return p.experience if p else []

    def get_portfolio_url(self, obj) -> str:
        p = self._get_profile(obj)
        return p.portfolio_url if p else ''

    def get_linkedin_url(self, obj) -> str:
        p = self._get_profile(obj)
        return p.linkedin_url if p else ''

    def get_github_url(self, obj) -> str:
        p = self._get_profile(obj)
        return p.github_url if p else ''

class ApplicationSerializer(serializers.ModelSerializer):
    candidate = ApplicationCandidateSerializer(read_only=True)
    job = JobSerializer(read_only=True)
    internal_notes = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id', 'job', 'candidate', 'resume', 'cover_letter',
            'status', 'internal_notes', 'interview_date',
            'applied_at', 'updated_at'
        ]
        read_only_fields = ['id', 'applied_at', 'updated_at']

    def get_internal_notes(self, obj) -> str:
        request = self.context.get('request')
        # Only recruiter of the job or admin can see internal notes
        if request and request.user and request.user.is_authenticated:
            recruiter = getattr(getattr(getattr(obj, 'job', None), 'company', None), 'recruiter', None)
            if request.user.role == UserRole.ADMIN or recruiter == request.user:
                return obj.internal_notes
        return None

class ApplicationCreateSerializer(serializers.ModelSerializer):
    job_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Application
        fields = ['job_id', 'resume', 'cover_letter']

    def validate(self, attrs):
        user = self.context['request'].user
        job_id = attrs.get('job_id')
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise serializers.ValidationError({"job_id": "Job posting does not exist."})

        if job.status != 'PUBLISHED':
            raise serializers.ValidationError({"job_id": "Cannot apply to a job that is not actively published."})

        if Application.objects.filter(job=job, candidate=user).exists():
            raise serializers.ValidationError({"non_field_errors": ["You have already applied for this job."]})

        attrs['job'] = job
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data.pop('job_id', None)
        application = Application.objects.create(candidate=user, **validated_data)
        return application

class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['status', 'internal_notes', 'interview_date']

    def update(self, instance, validated_data):
        old_status = instance.status
        instance = super().update(instance, validated_data)

        # Send notification to candidate if status changed
        if old_status != instance.status:
            from apps.notifications.services import create_notification
            create_notification(
                user=instance.candidate,
                title="Application Status Updated",
                message=f"Your application for {instance.job.title} at {instance.job.company.name} has been updated to '{instance.get_status_display()}'.",
                notification_type='STATUS_UPDATE',
                data={'application_id': str(instance.id), 'job_id': str(instance.job.id), 'status': instance.status}
            )
        return instance

