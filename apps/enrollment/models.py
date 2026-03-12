from django.db import models
from django.conf import settings


class Enrollment(models.Model):
    """
    Course enrollment record.
    Mirrors Moodle's mdl_user_enrolments + mdl_enrol.
    """
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    ROLE_STUDENT = 'student'
    ROLE_TEACHER = 'teacher'
    ROLE_ASSISTANT = 'assistant'
    ROLE_OBSERVER = 'observer'

    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_TEACHER, 'Teacher'),
        (ROLE_ASSISTANT, 'Teaching Assistant'),
        (ROLE_OBSERVER, 'Observer'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments'
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='enrollments'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='enrollments_created'
    )
    time_start = models.DateTimeField(null=True, blank=True)
    time_end = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'elening_enrollments'
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f'{self.user} enrolled in {self.course} ({self.role})'

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE


class StudyList(models.Model):
    """
    Personal study list: students can add courses they want to access later.
    TPF: "Add materials to their personal study list".
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_list_entries'
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='study_list_entries'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'elening_study_list'
        unique_together = ('user', 'course')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.user} → {self.course}'


class EnrollmentKey(models.Model):
    """Enrollment key (password) management for courses."""
    course = models.OneToOneField(
        'courses.Course', on_delete=models.CASCADE, related_name='enrollment_key_obj'
    )
    key = models.CharField(max_length=50)
    max_uses = models.IntegerField(default=0, help_text='0 = unlimited')
    use_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'elening_enrollment_keys'

    def __str__(self):
        return f'Key for {self.course}'
