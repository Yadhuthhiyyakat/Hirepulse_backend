from rest_framework import serializers
from .models import Company

class CompanySerializer(serializers.ModelSerializer):
    recruiter_name = serializers.CharField(source='recruiter.full_name', read_only=True)
    recruiter_email = serializers.ReadOnlyField(source='recruiter.email')
    jobs_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'recruiter', 'recruiter_name', 'recruiter_email',
            'name', 'logo', 'description', 'website', 'industry',
            'location', 'company_size', 'founded_year',
            'jobs_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'recruiter', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        if hasattr(data, '_mutable'):
            data = data.copy()
        elif isinstance(data, dict):
            data = dict(data)

        # Normalize website URL: auto-prefix with https:// if scheme is missing
        website = data.get('website')
        if website and isinstance(website, str):
            website = website.strip()
            if website.lower() in ('null', 'undefined'):
                data['website'] = ''
            elif website and not website.startswith(('http://', 'https://')):
                data['website'] = f'https://{website}'

        return super().to_internal_value(data)

    def get_jobs_count(self, obj) -> int:
        # We can annotate or count active jobs
        return getattr(obj, 'active_jobs_count', obj.jobs.filter(status='PUBLISHED').count())

