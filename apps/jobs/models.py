from django.db import models
from django.conf import settings
from apps.common.models import TimeStampedModel
from apps.companies.models import Company

class JobType(models.TextChoices):
    FULL_TIME = 'FULL_TIME', 'Full-time'
    PART_TIME = 'PART_TIME', 'Part-time'
    CONTRACT = 'CONTRACT', 'Contract'
    INTERNSHIP = 'INTERNSHIP', 'Internship'

class WorkMode(models.TextChoices):
    REMOTE = 'REMOTE', 'Remote'
    HYBRID = 'HYBRID', 'Hybrid'
    ONSITE = 'ONSITE', 'On-site'

class ExperienceLevel(models.TextChoices):
    ENTRY = 'ENTRY', 'Entry Level'
    JUNIOR = 'JUNIOR', 'Junior'
    MID = 'MID', 'Mid Level'
    SENIOR = 'SENIOR', 'Senior'
    LEAD = 'LEAD', 'Lead'

class JobStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PUBLISHED = 'PUBLISHED', 'Published'
    CLOSED = 'CLOSED', 'Closed'

class Job(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    location = models.CharField(max_length=255, db_index=True)
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME, db_index=True)
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices, default=WorkMode.REMOTE, db_index=True)
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.MID, db_index=True)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.PUBLISHED, db_index=True)

    class Meta:
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['location', 'job_type', 'work_mode']),
        ]

    def __str__(self):
        return f"{self.title} at {self.company.name}"

class SavedJob(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by_users')

    class Meta:
        verbose_name = 'Saved Job'
        verbose_name_plural = 'Saved Jobs'
        unique_together = ('user', 'job')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} saved {self.job.title}"

