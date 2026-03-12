from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.utils import timezone
from apps.courses.models import Course
from apps.assignments.models import Submission
from apps.quizzes.models import QuizAttempt
from apps.users.mixins import TeacherRequiredMixin
from .models import Enrollment, StudyList


@login_required
def enroll_course(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk, visible=True)

    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('courses:content', pk=course_pk)

    if course.is_full:
        messages.error(request, 'This course is full.')
        return redirect('courses:detail', pk=course_pk)

    if course.enrollment_type == Course.ENROL_MANUAL:
        messages.info(request, 'This course requires manual enrollment. Please contact the instructor.')
        return redirect('courses:detail', pk=course_pk)

    if course.enrollment_type == Course.ENROL_INVITE:
        messages.error(request, 'This course requires an invitation.')
        return redirect('courses:detail', pk=course_pk)

    # Open enrollment with key: show form on GET, validate key on POST
    if course.enrollment_type == Course.ENROL_OPEN and course.enrolment_key:
        if request.method != 'POST':
            return render(request, 'enrollment/enroll_key.html', {'course': course})
        key = request.POST.get('enrolment_key', '').strip()
        if key != course.enrolment_key:
            messages.error(request, 'Incorrect enrollment key.')
            return render(request, 'enrollment/enroll_key.html', {'course': course})
        # Key correct; fall through to create enrollment below

    # Open enrollment (with or without key): require POST to create enrollment
    if request.method != 'POST':
        return redirect('courses:detail', pk=course_pk)

    Enrollment.objects.create(
        user=request.user,
        course=course,
        role=Enrollment.ROLE_STUDENT,
        status=Enrollment.STATUS_ACTIVE,
        enrolled_by=request.user,
    )
    messages.success(request, f'You have successfully enrolled in "{course.fullname}".')
    return redirect('courses:content', pk=course_pk)


@login_required
def unenroll_course(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)

    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, f'You have closed/unenrolled from "{course.fullname}".')
        return redirect('enrollment:my_courses')

    return render(request, 'enrollment/unenroll_confirm.html', {'course': course})


class MyCoursesView(LoginRequiredMixin, ListView):
    template_name = 'enrollment/my_courses.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        return Enrollment.objects.filter(
            user=self.request.user, status=Enrollment.STATUS_ACTIVE
        ).select_related('course', 'course__category').order_by('-enrolled_at')


@login_required
def study_list_add(request, course_pk):
    """Add a course to the student's personal study list."""
    course = get_object_or_404(Course, pk=course_pk, visible=True)
    if Enrollment.objects.filter(user=request.user, course=course, status=Enrollment.STATUS_ACTIVE).exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('courses:detail', pk=course_pk)
    obj, created = StudyList.objects.get_or_create(user=request.user, course=course)
    if created:
        messages.success(request, f'"{course.fullname}" added to your study list.')
    next_url = request.GET.get('next') or request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url and next_url.strip():
        return redirect(next_url)
    return redirect('courses:detail', pk=course_pk)


@login_required
def study_list_remove(request, course_pk):
    """Remove a course from the student's personal study list."""
    course = get_object_or_404(Course, pk=course_pk)
    StudyList.objects.filter(user=request.user, course=course).delete()
    messages.success(request, f'"{course.fullname}" removed from your study list.')
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url and next_url.strip():
        return redirect(next_url)
    return redirect('enrollment:study_list')


class StudyListView(LoginRequiredMixin, ListView):
    """Personal study list: courses the user has saved for later."""
    template_name = 'enrollment/study_list.html'
    context_object_name = 'study_list_entries'

    def get_queryset(self):
        return StudyList.objects.filter(
            user=self.request.user
        ).select_related('course', 'course__category').order_by('-added_at')


class AssignmentsDoneView(LoginRequiredMixin, ListView):
    """List of assignments the student has submitted (assignments done)."""
    template_name = 'enrollment/assignments_done.html'
    context_object_name = 'submissions'
    paginate_by = 20

    def get_queryset(self):
        enrolled_course_ids = Enrollment.objects.filter(
            user=self.request.user, status=Enrollment.STATUS_ACTIVE
        ).values_list('course_id', flat=True)
        return (
            Submission.objects.filter(
                user=self.request.user,
                status=Submission.STATUS_SUBMITTED,
                assignment__course_id__in=enrolled_course_ids,
                assignment__visible=True,
            )
            .select_related('assignment', 'assignment__course')
            .order_by('-submitted_at', '-modified_at')
        )


class QuizzesDoneView(LoginRequiredMixin, ListView):
    """List of quizzes the student has finished (quizzes done)."""
    template_name = 'enrollment/quizzes_done.html'
    context_object_name = 'attempts'
    paginate_by = 20

    def get_queryset(self):
        enrolled_course_ids = Enrollment.objects.filter(
            user=self.request.user, status=Enrollment.STATUS_ACTIVE
        ).values_list('course_id', flat=True)
        return (
            QuizAttempt.objects.filter(
                user=self.request.user,
                state=QuizAttempt.STATE_FINISHED,
                quiz__course_id__in=enrolled_course_ids,
                quiz__visible=True,
                preview=False,
            )
            .select_related('quiz', 'quiz__course')
            .order_by('-time_finish', '-time_start')
        )


class InstructorEnrollmentsView(TeacherRequiredMixin, ListView):
    """Instructor: enrollments across courses they teach."""
    template_name = 'enrollment/instructor_enrollments.html'
    context_object_name = 'enrollments'
    paginate_by = 25

    def get_queryset(self):
        return (
            Enrollment.objects.filter(
                course__teacher=self.request.user,
                status=Enrollment.STATUS_ACTIVE,
            )
            .select_related('user', 'course')
            .order_by('-enrolled_at')
        )
