from django.contrib import admin
from .models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'recruiter', 'industry', 'location', 'company_size', 'created_at')
    list_filter = ('industry', 'company_size')
    search_fields = ('name', 'description', 'location', 'recruiter__email')

