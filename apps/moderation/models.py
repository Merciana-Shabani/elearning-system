from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class InstructorRoleApplication(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="instructor_role_applications",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    motivation = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instructor_role_applications_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    decision_reason = models.TextField(blank=True)

    class Meta:
        db_table = "elening_instructor_role_applications"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.user} ({self.status})"


class ContentReport(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="content_reports_filed"
    )
    reason = models.TextField()

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="content_reports_reviewed"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        db_table = "elening_content_reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report #{self.pk} ({self.status})"


class ModerationDispute(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
    ]

    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="disputes_opened"
    )
    against_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="disputes_against"
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="disputes_closed"
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closure_notes = models.TextField(blank=True)

    class Meta:
        db_table = "elening_moderation_disputes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Dispute #{self.pk} ({self.status})"


class ModerationAction(models.Model):
    ACTION_WARN = "warn"
    ACTION_SUSPEND = "suspend"
    ACTION_BAN = "ban"

    ACTION_CHOICES = [
        (ACTION_WARN, "Warning"),
        (ACTION_SUSPEND, "Suspend"),
        (ACTION_BAN, "Ban"),
    ]

    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="moderation_actions_made"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="moderation_actions_received"
    )
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "elening_moderation_actions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action_type} for {self.user_id} ({self.created_at.date()})"

    def apply(self):
        target = self.user
        if self.action_type == self.ACTION_SUSPEND:
            target.is_suspended = True
            target.save(update_fields=["is_suspended", "updated_at"])
        elif self.action_type == self.ACTION_BAN:
            target.is_active = False
            target.save(update_fields=["is_active"])
        return target

    @classmethod
    def expire_suspensions(cls):
        now = timezone.now()
        qs = cls.objects.filter(action_type=cls.ACTION_SUSPEND, expires_at__isnull=False, expires_at__lte=now)
        user_ids = list(qs.values_list("user_id", flat=True).distinct())
        if not user_ids:
            return 0
        from apps.users.models import User
        User.objects.filter(id__in=user_ids, is_suspended=True).update(is_suspended=False)
        return len(user_ids)

