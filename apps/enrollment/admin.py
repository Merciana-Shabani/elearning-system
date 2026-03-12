from django.contrib import admin
from .models import Enrollment, EnrollmentKey


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'role', 'status', 'enrolled_at', 'last_accessed']
    list_filter = ['status', 'role', 'course']
    search_fields = ['user__email', 'user__first_name', 'course__fullname']
    ordering = ['-enrolled_at']
    raw_id_fields = ['user', 'course', 'enrolled_by']


@admin.register(EnrollmentKey)
class EnrollmentKeyAdmin(admin.ModelAdmin):
    list_display = ['course', 'key', 'max_uses', 'use_count', 'expires_at']
