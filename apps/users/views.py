from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView, UpdateView, ListView
from django.urls import reverse_lazy
from .models import User, UserProfile
from .forms import UserUpdateForm, ProfileUpdateForm
from django.views.decorators.http import require_POST


class UserProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_user = self.get_object()
        context['enrolled_courses'] = target_user.enrollments.filter(
            status='active'
        ).select_related('course')
        context['is_own_profile'] = self.request.user == target_user
        return context


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.filter(is_active=True, is_suspended=False)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                first_name__icontains=q
            ) | qs.filter(
                last_name__icontains=q
            ) | qs.filter(
                email__icontains=q
            )
        if self.request.GET.get('sort') == 'recent':
            return qs.order_by('-date_joined')
        return qs.order_by('last_name', 'first_name')


@login_required
def edit_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('users:profile', pk=request.user.pk)
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(request, 'users/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
def user_dashboard(request, pk):
    """Show the dashboard for user pk. Users can only view their own dashboard."""
    # Moderators should use the dedicated moderation dashboard instead.
    if request.user.is_moderator:
        return redirect('moderation:dashboard')
    if request.user.pk != pk:
        return redirect('users:user_dashboard', pk=request.user.pk)
    return dashboard(request)


@login_required
def dashboard(request):
    """Render the current user's personal dashboard (role-based content)."""
    from django.utils import timezone
    from apps.courses.models import Course, CourseModuleCompletion, CourseCertificate, Document, SavedDocument
    from apps.enrollment.models import Enrollment
    user = request.user

    enrolled_courses = user.enrollments.filter(
        status='active'
    ).select_related('course').order_by('-enrolled_at')[:6]

    # Normal Staff: documents library access (no full student LMS dashboard)
    if user.is_normal_staff:
        total_documents = Document.objects.filter(visible=True).count()
        saved_documents = SavedDocument.objects.filter(user=user).count()
        context = {
            'total_documents': total_documents,
            'saved_documents': saved_documents,
            'enrolled_courses': enrolled_courses,
        }
        return render(request, 'dashboard_normal_staff.html', context)

    taught_courses = []
    if user.is_instructor:
        taught_courses = user.taught_courses.filter(
            visible=True
        ).order_by('-created_at')[:6]

    # Student-only: dedicated student dashboard
    if user.is_student and not user.is_instructor:
        from django.db.models import Q
        from apps.assignments.models import Assignment, Submission
        from apps.grades.models import Grade
        from apps.conferences.models import ConferenceRoom
        from apps.quizzes.models import Quiz, QuizAttempt
        enrolled_course_ids = list(
            user.enrollments.filter(status='active').values_list('course_id', flat=True)
        )

        new_courses = Course.objects.filter(
            visible=True
        ).exclude(
            pk__in=enrolled_course_ids
        ).select_related('category', 'teacher').order_by('-created_at')[:6]

        study_list_entries = list(
            user.study_list_entries.select_related('course', 'course__category').order_by('-added_at')[:6]
        )
        study_list_course_ids = set(user.study_list_entries.values_list('course_id', flat=True))

        now = timezone.now()
        # Progress per enrolled course (percentage based on completed modules)
        enrollment_progress = []
        if enrolled_courses:
            for enrollment in enrolled_courses:
                c = enrollment.course
                total_modules = c.modules.count()
                if total_modules == 0:
                    pct = 0
                else:
                    completed = CourseModuleCompletion.objects.filter(
                        user=user, module__course=c
                    ).count()
                    pct = int((completed / total_modules) * 100) if completed else 0
                enrollment_progress.append((enrollment, pct))

        # Certificates already issued to this student
        my_certificates = list(
            CourseCertificate.objects.filter(user=user).select_related('course').order_by('-issued_at')[:5]
        )
        pending_with_status = []
        overdue_list = []
        upcoming_conferences = []
        recent_grades = []
        assignments_done_count = 0
        quizzes_done_count = 0
        quizzes_done_list = []
        upcoming_quizzes = []

        if enrolled_course_ids:
            pending_assignments = Assignment.objects.filter(
                course_id__in=enrolled_course_ids,
                visible=True
            ).select_related('course').order_by('due_date')[:8]
            for a in pending_assignments:
                if a.due_date and a.due_date < now:
                    continue
                sub = Submission.objects.filter(
                    assignment=a, user=user, latest=True
                ).first()
                pending_with_status.append({
                    'assignment': a,
                    'submission': sub,
                    'submitted': sub and sub.status == Submission.STATUS_SUBMITTED,
                    'overdue': a.due_date and a.due_date < now,
                })
            overdue_assignments = Assignment.objects.filter(
                course_id__in=enrolled_course_ids,
                visible=True,
                due_date__lt=now
            ).select_related('course')
            submitted_ids = set(
                Submission.objects.filter(
                    user=user, assignment__in=overdue_assignments,
                    status=Submission.STATUS_SUBMITTED
                ).values_list('assignment_id', flat=True)
            )
            overdue_list = [
                a for a in overdue_assignments[:5]
                if a.pk not in submitted_ids
            ]
            upcoming_conferences = list(ConferenceRoom.objects.filter(
                course_id__in=enrolled_course_ids,
                scheduled_at__gte=now
            ).select_related('course').order_by('scheduled_at')[:5])
            recent_grades = list(Grade.objects.filter(
                user=user,
                item__course_id__in=enrolled_course_ids,
                finalgrade__isnull=False
            ).select_related('item', 'item__course').order_by('-updated_at')[:5])

            # Assignments done (submitted)
            assignments_done_count = Submission.objects.filter(
                user=user,
                status=Submission.STATUS_SUBMITTED,
                assignment__course_id__in=enrolled_course_ids,
            ).count()

            # Quizzes: done (finished attempts) and upcoming (not yet closed)
            finished_attempts = QuizAttempt.objects.filter(
                user=user,
                state=QuizAttempt.STATE_FINISHED,
                quiz__course_id__in=enrolled_course_ids,
            ).select_related('quiz', 'quiz__course').order_by('-time_finish')
            seen_quiz_ids = set()
            for att in finished_attempts[:20]:
                if att.quiz_id not in seen_quiz_ids:
                    seen_quiz_ids.add(att.quiz_id)
                    quizzes_done_list.append({'quiz': att.quiz, 'finished_at': att.time_finish})
                if len(quizzes_done_list) >= 5:
                    break
            quizzes_done_count = QuizAttempt.objects.filter(
                user=user,
                state=QuizAttempt.STATE_FINISHED,
                quiz__course_id__in=enrolled_course_ids,
            ).values_list('quiz_id', flat=True).distinct().count()

            upcoming_quizzes = list(
                Quiz.objects.filter(
                    course_id__in=enrolled_course_ids,
                    visible=True,
                ).filter(Q(time_close__isnull=True) | Q(time_close__gte=now))
                .select_related('course')
                .order_by('time_close')[:5]
            )

        context = {
            'enrolled_courses': enrolled_courses,
            'enrollment_progress': enrollment_progress,
            'new_courses': new_courses,
            'study_list_entries': study_list_entries,
            'study_list_course_ids': study_list_course_ids,
            'pending_assignments': pending_with_status,
            'overdue_assignments': overdue_list,
            'upcoming_conferences': upcoming_conferences,
            'recent_grades': recent_grades,
            'enrolled_count': len(enrolled_course_ids),
            'certificates': my_certificates,
            'certificates_count': len(my_certificates),
            'assignments_done_count': assignments_done_count,
            'overdue_count': len(overdue_list),
            'study_list_count': len(study_list_entries),
            'upcoming_conferences_count': len(upcoming_conferences) if enrolled_course_ids else 0,
            'quizzes_done_count': quizzes_done_count,
            'quizzes_done_list': quizzes_done_list,
            'upcoming_quizzes': upcoming_quizzes,
        }
        return render(request, 'dashboard_student.html', context)

    # Instructor dashboard
    if user.is_instructor:
        my_course_ids = list(user.taught_courses.values_list('pk', flat=True))
        courses_teaching_count = len(my_course_ids)
        total_enrollments_my = (
            Enrollment.objects.filter(course_id__in=my_course_ids, status='active').count()
            if my_course_ids else 0
        )
        pending_submissions_my = (
            user.taught_courses.filter(status=Course.STATUS_SUBMITTED).count()
        )
        from apps.quizzes.models import Quiz
        from apps.assignments.models import Assignment
        from apps.conferences.models import ConferenceRoom
        from django.utils import timezone as tz
        quizzes_count = Quiz.objects.filter(course_id__in=my_course_ids).count() if my_course_ids else 0
        assignments_count = Assignment.objects.filter(course_id__in=my_course_ids, visible=True).count() if my_course_ids else 0
        live_sessions_upcoming = (
            ConferenceRoom.objects.filter(
                course_id__in=my_course_ids,
                scheduled_at__gte=tz.now()
            ).count() if my_course_ids else 0
        )
        context = {
            'enrolled_courses': enrolled_courses,
            'taught_courses': taught_courses,
            'courses_teaching_count': courses_teaching_count,
            'total_enrollments_my': total_enrollments_my,
            'pending_submissions_my': pending_submissions_my,
            'quizzes_count': quizzes_count,
            'assignments_count': assignments_count,
            'live_sessions_upcoming': live_sessions_upcoming,
        }
        return render(request, 'dashboard_instructor.html', context)

    # Moderator / Admin dashboard
    recent_users = []
    total_users = 0
    total_courses = 0
    total_enrollments = 0
    if user.is_moderator:
        recent_users = User.objects.filter(
            is_active=True
        ).order_by('-date_joined')[:8]
        total_users = User.objects.filter(is_active=True).count()
        total_courses = Course.objects.filter(visible=True).count()
        total_enrollments = Enrollment.objects.filter(status='active').count()

    context = {
        'enrolled_courses': enrolled_courses,
        'taught_courses': taught_courses,
        'recent_users': recent_users,
        'total_users': total_users,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
    }
    return render(request, 'dashboard.html', context)


@require_POST
def set_signup_type(request):
    """
    Step 1 of signup: store chosen user type in session, then redirect to allauth signup.
    """
    role = request.POST.get('signup_role', User.ROLE_STUDENT)
    if role not in {User.ROLE_STUDENT, User.ROLE_TEACHER, User.ROLE_MODERATOR}:
        role = User.ROLE_STUDENT

    student_type = request.POST.get('signup_student_type', User.STUDENT_DPA)
    if role == User.ROLE_STUDENT and student_type not in {User.STUDENT_DPA, User.STUDENT_NORMAL_STAFF}:
        student_type = User.STUDENT_DPA
    if role != User.ROLE_STUDENT:
        student_type = ''

    request.session['signup_role'] = role
    request.session['signup_student_type'] = student_type
    request.session.modified = True
    return redirect('account_signup')


@require_POST
def clear_signup_type(request):
    """Allow user to restart signup step 1."""
    request.session.pop('signup_role', None)
    request.session.pop('signup_student_type', None)
    request.session.modified = True
    return redirect('account_signup')