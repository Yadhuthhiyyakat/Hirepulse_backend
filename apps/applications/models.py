from django.db import models
from django.conf import settings
from apps.common.models import TimeStampedModel
from apps.jobs.models import Job
from apps.common.utils import validate_file_size, validate_file_extension

def application_resume_validator(file):
    validate_file_size(file)
    validate_file_extension(file, ['.pdf', '.doc', '.docx'])

class ApplicationStatus(models.TextChoices):
    APPLIED = 'APPLIED', 'Applied'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
    INTERVIEW = 'INTERVIEW', 'Interview'
    REJECTED = 'REJECTED', 'Rejected'
    HIRED = 'HIRED', 'Hired'

class Application(TimeStampedModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    resume = models.FileField(upload_to='resumes/applications/', validators=[application_resume_validator])
    cover_letter = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.APPLIED,
        db_index=True
    )
    internal_notes = models.TextField(blank=True, help_text="Recruiter internal notes")
    interview_date = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        unique_together = ('job', 'candidate')
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['status', 'applied_at']),
            models.Index(fields=['job', 'status']),
        ]

    def __str__(self):
        return f"{self.candidate.email} - {self.job.title} ({self.status})"

