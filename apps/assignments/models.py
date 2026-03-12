from django.db import models
from django.conf import settings
from ckeditor_uploader.fields import RichTextUploadingField


class Assignment(models.Model):
    """
    Assignment activity.
    Mirrors Moodle's mdl_assign table.
    """
    SUBMISSION_ONLINE_TEXT = 'onlinetext'
    SUBMISSION_FILE = 'file'
    SUBMISSION_BOTH = 'both'

    SUBMISSION_CHOICES = [
        (SUBMISSION_ONLINE_TEXT, 'Online text'),
        (SUBMISSION_FILE, 'File upload'),
        (SUBMISSION_BOTH, 'Online text & file'),
    ]

    GRADING_SIMPLE = 'simple'
    GRADING_RUBRIC = 'rubric'
    GRADING_GUIDE = 'guide'

    GRADING_CHOICES = [
        (GRADING_SIMPLE, 'Simple direct grading'),
        (GRADING_RUBRIC, 'Rubric'),
        (GRADING_GUIDE, 'Marking guide'),
    ]

    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='assignments'
    )
    name = models.CharField(max_length=255)
    intro = RichTextUploadingField(verbose_name='Description')
    intro_attachments = models.FileField(upload_to='assignment_intros/', blank=True, null=True)
    rubric_criteria = RichTextUploadingField(
        blank=True,
        help_text='Marking rubric: criteria and point breakdown for grading.'
    )
    submission_type = models.CharField(
        max_length=20, choices=SUBMISSION_CHOICES, default=SUBMISSION_FILE
    )
    grading_method = models.CharField(
        max_length=20, choices=GRADING_CHOICES, default=GRADING_SIMPLE
    )
    max_grade = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    passing_grade = models.DecimalField(max_digits=6, decimal_places=2, default=50)
    allow_submissions_from = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    cut_off_date = models.DateTimeField(null=True, blank=True)
    max_attempts = models.IntegerField(default=-1, help_text='-1 = unlimited')
    max_files = models.IntegerField(default=1)
    max_file_size = models.IntegerField(default=0, help_text='Max size in bytes, 0=unlimited')
    allowed_file_types = models.CharField(
        max_length=255, blank=True, help_text='e.g. .pdf,.docx'
    )
    team_submission = models.BooleanField(default=False)
    require_submission_statement = models.BooleanField(default=False)
    blind_marking = models.BooleanField(default=False)
    send_late_notifications = models.BooleanField(default=True)
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_assignments'
        ordering = ['due_date', 'name']

    def __str__(self):
        return f'{self.name} ({self.course.shortname})'

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date and timezone.now() > self.due_date


class Submission(models.Model):
    """
    Student submission for an assignment.
    Mirrors Moodle's mdl_assign_submission.
    """
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_REOPENED = 'reopened'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_REOPENED, 'Reopened'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    online_text = RichTextUploadingField(blank=True)
    file = models.FileField(upload_to='submissions/', blank=True, null=True)
    attempt_number = models.IntegerField(default=0)
    latest = models.BooleanField(default=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_submissions'
        ordering = ['-modified_at']

    def __str__(self):
        return f'{self.user} → {self.assignment}'


class AssignmentGrade(models.Model):
    """Grade for a submission."""
    submission = models.OneToOneField(
        Submission, on_delete=models.CASCADE, related_name='grade'
    )
    grader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='graded_submissions'
    )
    grade = models.DecimalField(max_digits=6, decimal_places=2)
    feedback = RichTextUploadingField(blank=True)
    graded_at = models.DateTimeField(auto_now=True)
    released = models.BooleanField(default=False)

    class Meta:
        db_table = 'elening_assignment_grades'

    def __str__(self):
        return f'{self.submission} grade: {self.grade}'
