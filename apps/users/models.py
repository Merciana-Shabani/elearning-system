from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Mirrors Moodle's mdl_user table with additional fields.
    """
    ROLE_STUDENT = 'student'
    ROLE_TEACHER = 'teacher'
    ROLE_MODERATOR = 'moderator'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_TEACHER, 'Instructor'),
        (ROLE_MODERATOR, 'Moderator'),
        (ROLE_ADMIN, 'Administrator'),
    ]

    STUDENT_DPA = 'dpa'
    STUDENT_NORMAL_STAFF = 'normal_staff'
    STUDENT_TYPE_CHOICES = [
        (STUDENT_DPA, 'DPA Student (Diploma in Police Administration)'),
        (STUDENT_NORMAL_STAFF, 'Normal Staff (Police officers – training materials access)'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    student_type = models.CharField(
        max_length=20,
        choices=STUDENT_TYPE_CHOICES,
        blank=True,
        help_text='For students: DPA program or Normal Staff (training materials only).',
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=2, blank=True)
    timezone = models.CharField(max_length=100, default='UTC')
    lang = models.CharField(max_length=10, default='en')
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    idnumber = models.CharField(max_length=255, blank=True, help_text='Institutional ID number')
    staff_code = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text='Unique staff identifier for Instructors/Moderators (e.g., service/employee number).',
    )
    department = models.CharField(max_length=255, blank=True)
    institution = models.CharField(max_length=255, blank=True)
    is_suspended = models.BooleanField(default=False)
    can_teach = models.BooleanField(
        default=False,
        help_text='If True, user can create and manage courses (instructor capability). Moderators can have this to also act as instructors; instructors have it via role=teacher.',
    )
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'elening_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'

    def get_absolute_url(self):
        return reverse('users:profile', kwargs={'pk': self.pk})

    @property
    def is_teacher(self):
        """True if user acts as Instructor (role=teacher, moderator, admin, or explicitly can_teach)."""
        return (
            self.role in (self.ROLE_TEACHER, self.ROLE_MODERATOR, self.ROLE_ADMIN)
            or self.can_teach
        )

    @property
    def is_instructor(self):
        """Alias for instructor capability."""
        return self.is_teacher

    @property
    def became_instructor_via_application(self):
        """True if this user has an approved InstructorRoleApplication (moderator-approved)."""
        if not self.is_instructor:
            return False
        from apps.moderation.models import InstructorRoleApplication
        return InstructorRoleApplication.objects.filter(
            user=self, status=InstructorRoleApplication.STATUS_APPROVED
        ).exists()

    def get_instructor_origin_display(self):
        """How they got Instructor role: 'Approved via application' or 'Registered as Instructor'."""
        if not self.is_instructor:
            return ''
        return 'Approved via application' if self.became_instructor_via_application else 'Registered as Instructor'

    @property
    def can_manage_courses(self):
        """Instructors (role=teacher or can_teach) and admins/staff can create/manage courses."""
        return self.is_instructor or self.is_admin_role or self.is_staff

    @property
    def can_manage_live_sessions(self):
        """Instructors, moderators, and admins/staff can create/manage live sessions."""
        return self.is_instructor or self.is_moderator or self.is_admin_role or self.is_staff

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT

    @property
    def is_moderator(self):
        return self.role in [self.ROLE_MODERATOR, self.ROLE_ADMIN]

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_dpa_student(self):
        return self.is_student and self.student_type == self.STUDENT_DPA

    @property
    def is_normal_staff(self):
        return self.is_student and self.student_type == self.STUDENT_NORMAL_STAFF

    @property
    def full_name(self):
        return self.get_full_name() or self.username


class UserProfile(models.Model):
    """Extended profile information for users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    website = models.URLField(blank=True)
    interests = models.TextField(blank=True)
    skype = models.CharField(max_length=50, blank=True)
    aim = models.CharField(max_length=50, blank=True)
    msn = models.CharField(max_length=50, blank=True)
    yahoo = models.CharField(max_length=50, blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'elening_user_profiles'

    def __str__(self):
        return f'Profile of {self.user}'


class UserPreference(models.Model):
    """User preferences (mirrors mdl_user_preferences)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preferences')
    name = models.CharField(max_length=255)
    value = models.TextField()

    class Meta:
        db_table = 'elening_user_preferences'
        unique_together = ('user', 'name')

    def __str__(self):
        return f'{self.user.username}: {self.name}'
