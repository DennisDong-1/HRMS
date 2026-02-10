from django.contrib import admin

from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("candidate", "job", "match_score", "decision", "screened_at")
    search_fields = ("candidate__full_name", "candidate__email", "job__title")
    list_filter = ("decision", "screened_at", "job")

