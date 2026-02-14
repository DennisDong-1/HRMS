from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """
    Simple admin configuration for the Job model.
    """

    list_display = ("title", "required_experience", "created_by", "created_at")
    search_fields = ("title", "required_skills", "created_by__email")
    list_filter = ("required_experience", "created_at")

