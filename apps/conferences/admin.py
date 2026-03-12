from django.contrib import admin
from .models import ConferenceRoom


@admin.register(ConferenceRoom)
class ConferenceRoomAdmin(admin.ModelAdmin):
    list_display = ['title', 'host', 'course', 'is_active', 'scheduled_at', 'created_at']
    list_filter = ['is_active', 'require_password']
    search_fields = ['title', 'host__email', 'course__fullname']
    readonly_fields = ['room_slug', 'started_at', 'ended_at', 'created_at', 'updated_at']
