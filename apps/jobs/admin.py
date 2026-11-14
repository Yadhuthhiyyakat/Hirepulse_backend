from django.contrib import admin
from .models import Job, SavedJob

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'work_mode', 'experience_level', 'status', 'created_at')
    list_filter = ('status', 'job_type', 'work_mode', 'experience_level')
    search_fields = ('title', 'description', 'company__name', 'location')

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'created_at')
    search_fields = ('user__email', 'job__title')

