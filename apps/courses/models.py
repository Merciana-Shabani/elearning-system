from django.db import models
from django.conf import settings
from django.urls import reverse
from ckeditor_uploader.fields import RichTextUploadingField


class CourseCategory(models.Model):
    """
    Hierarchical course categories.
    Mirrors Moodle's mdl_course_categories.
    """
    name = models.CharField(max_length=255)
    idnumber = models.CharField(max_length=100, blank=True)
    description = RichTextUploadingField(blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children'
    )
    sortorder = models.IntegerField(default=0)
    visible = models.BooleanField(default=True)
    depth = models.IntegerField(default=1)
    path = models.CharField(max_length=255, blank=True)
    theme = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_course_categories'
        verbose_name = 'Course Category'
        verbose_name_plural = 'Course Categories'
        ordering = ['sortorder', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('courses:category', kwargs={'pk': self.pk})

    @property
    def course_count(self):
        return self.courses.filter(visible=True).count()


class Course(models.Model):
    """
    Core course model.
    Mirrors Moodle's mdl_course table.
    """
    FORMAT_TOPICS = 'topics'
    FORMAT_WEEKS = 'weeks'
    FORMAT_SOCIAL = 'social'
    FORMAT_SINGLEACTIVITY = 'singleactivity'

    FORMAT_CHOICES = [
        (FORMAT_TOPICS, 'Topics format'),
        (FORMAT_WEEKS, 'Weekly format'),
        (FORMAT_SOCIAL, 'Social format'),
        (FORMAT_SINGLEACTIVITY, 'Single activity format'),
    ]

    ENROL_OPEN = 'open'
    ENROL_MANUAL = 'manual'
    ENROL_INVITE = 'invite'

    ENROL_CHOICES = [
        (ENROL_OPEN, 'Open enrollment'),
        (ENROL_MANUAL, 'Manual enrollment (teacher approves)'),
        (ENROL_INVITE, 'Invitation only'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_PUBLISHED = 'published'
    STATUS_REJECTED = 'rejected'
    STATUS_NEEDS_REVISION = 'needs_revision'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted for approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_NEEDS_REVISION, 'Needs revision'),
    ]

    category = models.ForeignKey(
        CourseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses'
    )
    fullname = models.CharField(max_length=254, verbose_name='Full Name')
    shortname = models.CharField(max_length=255, unique=True, verbose_name='Short Name')
    idnumber = models.CharField(max_length=100, blank=True)
    summary = RichTextUploadingField(blank=True, verbose_name='Course Summary')
    image = models.ImageField(upload_to='course_images/', blank=True, null=True)
    format = models.CharField(max_length=21, choices=FORMAT_CHOICES, default=FORMAT_TOPICS)
    enrollment_type = models.CharField(max_length=20, choices=ENROL_CHOICES, default=ENROL_OPEN)
    enrolment_key = models.CharField(max_length=50, blank=True, help_text='Enrollment key/password')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    visible = models.BooleanField(default=True)
    startdate = models.DateField(null=True, blank=True)
    enddate = models.DateField(null=True, blank=True)
    lang = models.CharField(max_length=30, blank=True)
    theme = models.CharField(max_length=50, blank=True)
    max_students = models.PositiveIntegerField(default=0, help_text='0 = unlimited')
    completion_enabled = models.BooleanField(default=False)
    show_grades = models.BooleanField(default=True)
    show_activity_dates = models.BooleanField(default=True)
    news_items = models.IntegerField(default=5)
    sortorder = models.IntegerField(default=0)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='taught_courses'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT,
        help_text='Draft → Submit for approval → Moderator approves/rejects → Published'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courses_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    revision_requests = models.TextField(blank=True)
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses_returned_for_revision',
    )
    returned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_courses'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['fullname']

    def __str__(self):
        return self.fullname

    def get_absolute_url(self):
        return reverse('courses:detail', kwargs={'pk': self.pk})

    @property
    def is_published(self):
        """True if course is visible to students (moderator-approved)."""
        return self.status == self.STATUS_PUBLISHED

    @property
    def enrolled_count(self):
        return self.enrollments.filter(status='active').count()

    @property
    def is_full(self):
        if self.max_students == 0:
            return False
        return self.enrolled_count >= self.max_students

    @property
    def image_if_exists(self):
        """Return image field only if the file exists on disk (avoids 404 for missing uploads)."""
        if self.image and self.image.name:
            try:
                return self.image if self.image.storage.exists(self.image.name) else None
            except Exception:
                return None
        return None


class CourseSection(models.Model):
    """
    Course section (week or topic).
    Mirrors Moodle's mdl_course_sections.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    section = models.IntegerField(default=0, help_text='Section number (0=general)')
    name = models.CharField(max_length=255, blank=True)
    summary = RichTextUploadingField(blank=True)
    visible = models.BooleanField(default=True)
    availability = models.TextField(blank=True)
    sortorder = models.IntegerField(default=0)
    required_section = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='unlocks_sections',
        help_text='Learner must complete this section before accessing this one.'
    )

    class Meta:
        db_table = 'elening_course_sections'
        ordering = ['sortorder', 'section']
        unique_together = ('course', 'section')

    def __str__(self):
        return self.name or f'Section {self.section}'


class CourseAnnouncement(models.Model):
    """Announcement posted by instructor, visible to all enrolled students."""
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='announcements'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_announcements'
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'elening_course_announcements'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.course.shortname})'


class CourseModule(models.Model):
    """
    Course module (activity instance within a course).
    Mirrors Moodle's mdl_course_modules.
    """
    MODULE_PAGE = 'page'
    MODULE_ASSIGNMENT = 'assignment'
    MODULE_QUIZ = 'quiz'
    MODULE_FORUM = 'forum'
    MODULE_FILE = 'file'
    MODULE_URL = 'url'
    MODULE_LABEL = 'label'
    MODULE_VIDEO = 'video'
    MODULE_SCORM = 'scorm'

    MODULE_TYPE_CHOICES = [
        (MODULE_PAGE, 'Page'),
        (MODULE_ASSIGNMENT, 'Assignment'),
        (MODULE_QUIZ, 'Quiz'),
        (MODULE_FORUM, 'Forum'),
        (MODULE_FILE, 'File'),
        (MODULE_URL, 'URL'),
        (MODULE_LABEL, 'Label/Text'),
        (MODULE_VIDEO, 'Video'),
        (MODULE_SCORM, 'SCORM Package'),
    ]

    COMPLETION_NONE = 0
    COMPLETION_MANUAL = 1
    COMPLETION_AUTOMATIC = 2

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    section = models.ForeignKey(
        CourseSection, on_delete=models.SET_NULL, null=True, blank=True, related_name='modules'
    )
    module_type = models.CharField(max_length=20, choices=MODULE_TYPE_CHOICES)
    instance_id = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='FK to the specific activity table (quiz, assignment, etc.)'
    )
    name = models.CharField(max_length=255)
    visible = models.BooleanField(default=True)
    sortorder = models.IntegerField(default=0)
    indent = models.IntegerField(default=0)
    completion = models.IntegerField(default=COMPLETION_NONE)
    completion_view = models.BooleanField(default=False, help_text='Complete on view')
    availability = models.TextField(blank=True)
    required_module = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='unlocks_modules',
        help_text='Learner must complete this module before accessing this one.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_course_modules'
        ordering = ['section__sortorder', 'sortorder']

    def __str__(self):
        return f'{self.name} ({self.module_type}) in {self.course.shortname}'


class CourseModuleCompletion(models.Model):
    """Tracks completion of a course module by a user (for prerequisites and analytics)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='module_completions'
    )
    module = models.ForeignKey(
        CourseModule, on_delete=models.CASCADE, related_name='completions'
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'elening_course_module_completions'
        unique_together = ('user', 'module')
        ordering = ['-completed_at']

    def __str__(self):
        return f'{self.user} completed {self.module}'


class CoursePage(models.Model):
    """A static page resource inside a course."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='pages')
    name = models.CharField(max_length=255)
    intro = models.TextField(blank=True)
    content = RichTextUploadingField()
    display = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_course_pages'

    def __str__(self):
        return self.name


class CourseFile(models.Model):
    """File resource inside a course."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='course_files/')
    display = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'elening_course_files'

    def __str__(self):
        return self.name


class CourseCompletion(models.Model):
    """Tracks overall course completion per user."""
    STATUS_IN_PROGRESS = 'inprogress'
    STATUS_COMPLETE = 'complete'
    STATUS_COMPLETE_PASS = 'completedpass'
    STATUS_COMPLETE_FAIL = 'completedfail'

    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETE, 'Completed'),
        (STATUS_COMPLETE_PASS, 'Completed (Pass)'),
        (STATUS_COMPLETE_FAIL, 'Completed (Fail)'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_completions'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='completions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    timecompleted = models.DateTimeField(null=True, blank=True)
    reaggregate = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'elening_course_completions'
        unique_together = ('user', 'course')

    def __str__(self):
        return f'{self.user} - {self.course} ({self.status})'


class CourseCertificate(models.Model):
    """Certificate of completion issued (manually) to a student by an instructor."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates'
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='certificates_issued'
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='certificates_issued'
    )
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'elening_course_certificates'
        unique_together = ('user', 'course')
        ordering = ['-issued_at']

    def __str__(self):
        return f'{self.user} - {self.course} (issued {self.issued_at.date()})'


class Document(models.Model):
    """Standalone documents uploaded by instructors for Normal Staff access."""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='uploaded_documents'
    )
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'elening_documents'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class SavedDocument(models.Model):
    """Tracks documents saved by a user (auto-saved on download)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_documents'
    )
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='saved_by'
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # NOTE: 'elening_saved_documents' already exists in DB for course-file downloads.
        # Use a separate table for library-document saves.
        db_table = 'elening_saved_library_documents'
        unique_together = ('user', 'document')
        ordering = ['-saved_at']

    def __str__(self):
        return f'{self.user} saved {self.document}'
