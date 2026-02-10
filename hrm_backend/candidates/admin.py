from django.contrib import admin

from .models import Candidate


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """
    Admin configuration for Candidate model.
    """

    list_display = ("full_name", "applied_job", "match_score", "status", "created_at")
    search_fields = ("full_name", "email", "applied_job__title")
    list_filter = ("status", "created_at", "applied_job")

