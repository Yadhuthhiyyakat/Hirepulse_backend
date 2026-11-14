from rest_framework import serializers
from .models import Job, SavedJob, JobType, WorkMode, ExperienceLevel, JobStatus
from apps.companies.serializers import CompanySerializer
from apps.companies.models import Company

class JobCompanySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'logo', 'industry', 'location', 'website', 'company_size']

class JobSerializer(serializers.ModelSerializer):
    company = JobCompanySummarySerializer(read_only=True)
    is_saved = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'company', 'title', 'description', 'requirements',
            'responsibilities', 'skills', 'location', 'job_type',
            'work_mode', 'experience_level', 'salary_min', 'salary_max',
            'application_deadline', 'status', 'is_saved', 'has_applied',
            'applications_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_saved(self, obj) -> bool:
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            if hasattr(obj, '_prefetched_objects_cache') and 'saved_by_users' in obj._prefetched_objects_cache:
                return any(saved.user_id == request.user.id for saved in obj.saved_by_users.all())
            return obj.saved_by_users.filter(user=request.user).exists()
        return False

    def get_has_applied(self, obj) -> bool:
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            if hasattr(obj, '_prefetched_objects_cache') and 'applications' in obj._prefetched_objects_cache:
                return any(app.candidate_id == request.user.id for app in obj.applications.all())
            return obj.applications.filter(candidate=request.user).exists()
        return False

    def get_applications_count(self, obj) -> int:
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            # Only recruiter of this job or admin can see applications count
            recruiter = getattr(getattr(obj, 'company', None), 'recruiter', None)
            if recruiter == request.user or getattr(request.user, 'role', None) == 'ADMIN':
                return getattr(obj, 'active_applications_count', obj.applications.count())
        return None

class JobCreateUpdateSerializer(serializers.ModelSerializer):
    company_id = serializers.UUIDField(required=False)

    class Meta:
        model = Job
        fields = [
            'id', 'company_id', 'title', 'description', 'requirements',
            'responsibilities', 'skills', 'location', 'job_type',
            'work_mode', 'experience_level', 'salary_min', 'salary_max',
            'application_deadline', 'status'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        salary_min = attrs.get('salary_min')
        salary_max = attrs.get('salary_max')
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise serializers.ValidationError({"salary_max": "Maximum salary cannot be less than minimum salary."})
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        company_id = validated_data.pop('company_id', None)
        if company_id:
            try:
                company = Company.objects.get(id=company_id, recruiter=user)
            except Company.DoesNotExist:
                raise serializers.ValidationError({"company_id": "Company not found or does not belong to you."})
        else:
            company = Company.objects.filter(recruiter=user).first()
            if not company:
                raise serializers.ValidationError({"company": "You must create a company profile before posting a job."})

        job = Job.objects.create(company=company, **validated_data)
        return job

class SavedJobSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = SavedJob
        fields = ['id', 'job', 'created_at']
        read_only_fields = ['id', 'created_at']

