from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """
    Enhanced admin configuration for the Job model.
    
    Provides comprehensive filtering, search, and organized form layout
    for HR users managing job postings.
    """

    list_display = (
        "title",
        "status",
        "department",
        "location",
        "required_experience",
        "created_by",
        "created_at",
    )
    
    list_filter = (
        "status",
        "department",
        "created_at",
    )
    
    search_fields = (
        "title",
        "description",
        "required_skills",
        "department",
        "location",
    )
    
    readonly_fields = ("created_by", "created_at")
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "status", "description")
        }),
        ("Requirements", {
            "fields": ("required_skills", "required_experience")
        }),
        ("Organization", {
            "fields": ("department", "location")
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at"),
            "classes": ("collapse",),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Automatically set created_by when creating a new job through admin.
        """
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


