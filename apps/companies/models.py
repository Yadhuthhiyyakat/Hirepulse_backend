from django.db import models
from django.conf import settings
from apps.common.models import TimeStampedModel

class Company(TimeStampedModel):
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='companies'
    )
    name = models.CharField(max_length=255, db_index=True)
    logo = models.ImageField(upload_to='companies/', blank=True, null=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=150, blank=True, db_index=True)
    location = models.CharField(max_length=255, blank=True)
    company_size = models.CharField(max_length=50, blank=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

