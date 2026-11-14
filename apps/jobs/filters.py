import django_filters
from django.db.models import Q
from .models import Job, JobType, WorkMode, ExperienceLevel, JobStatus

class JobFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')
    location = django_filters.CharFilter(field_name='location', lookup_expr='icontains')
    job_type = django_filters.ChoiceFilter(choices=JobType.choices)
    work_mode = django_filters.ChoiceFilter(choices=WorkMode.choices)
    experience_level = django_filters.ChoiceFilter(choices=ExperienceLevel.choices)
    salary_min = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    skill = django_filters.CharFilter(method='filter_by_skill')
    company = django_filters.UUIDFilter(field_name='company__id')

    class Meta:
        model = Job
        fields = [
            'search', 'location', 'job_type', 'work_mode',
            'experience_level', 'salary_min', 'salary_max',
            'skill', 'company', 'status'
        ]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(company__name__icontains=value) |
            Q(location__icontains=value) |
            Q(skills__icontains=value)
        )

    def filter_by_skill(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(skills__icontains=value)

