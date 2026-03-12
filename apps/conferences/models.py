import uuid
from django.db import models
from django.conf import settings
from django.urls import reverse


class ConferenceRoom(models.Model):
    """
    A live video conference room powered by Jitsi Meet.
    Can be tied to a course or standalone.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='conference_rooms', null=True, blank=True
    )
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='hosted_rooms'
    )
    # UUID-based slug keeps the Jitsi room name unguessable
    room_slug = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Session duration in minutes (e.g. 120 for 2 hours, 300 for 5 hours).',
    )
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    require_password = models.BooleanField(default=False)
    room_password = models.CharField(max_length=50, blank=True)
    max_participants = models.PositiveIntegerField(
        default=0, help_text='0 = unlimited'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_conference_rooms'
        ordering = ['-scheduled_at', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('conferences:room', kwargs={'slug': self.room_slug})

    @property
    def jitsi_room_name(self):
        """Safe alphanumeric room name for Jitsi."""
        return f"elening-{self.room_slug.hex}"

    @property
    def is_scheduled(self):
        return self.scheduled_at is not None and not self.is_active and not self.ended_at

    @property
    def is_ended(self):
        return self.ended_at is not None
