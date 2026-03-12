from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView, ListView, CreateView
from django.utils import timezone
from .models import Assignment, Submission, AssignmentGrade
from .forms import SubmissionForm, GradeSubmissionForm, AssignmentCreateForm
from apps.enrollment.models import Enrollment
from apps.courses.models import Course, CourseModule
from apps.users.mixins import TeacherRequiredMixin


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Assignment
    template_name = 'assignments/assignment_detail.html'
    context_object_name = 'assignment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()
        user = self.request.user
        try:
            context['my_submission'] = Submission.objects.filter(
                assignment=assignment, user=user, latest=True
            ).latest('modified_at')
        except Submission.DoesNotExist:
            context['my_submission'] = None
        context['is_teacher'] = (
            assignment.course.teacher == user or user.is_staff
        )
        context['submission_form'] = SubmissionForm(instance=context['my_submission'])
        return context


@login_required
def submit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)

    if not Enrollment.objects.filter(
        user=request.user, course=assignment.course, status='active'
    ).exists():
        messages.error(request, 'You must be enrolled to submit.')
        return redirect('courses:detail', pk=assignment.course.pk)

    if assignment.cut_off_date and timezone.now() > assignment.cut_off_date:
        messages.error(request, 'The cut-off date has passed. Submissions are no longer accepted.')
        return redirect('assignments:detail', pk=pk)

    submission, _ = Submission.objects.get_or_create(
        assignment=assignment, user=request.user,
        defaults={'status': Submission.STATUS_DRAFT}
    )

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            sub = form.save(commit=False)
            if 'submit_final' in request.POST:
                sub.status = Submission.STATUS_SUBMITTED
                sub.submitted_at = timezone.now()
            sub.save()
            messages.success(request, 'Submission saved.')
            return redirect('assignments:detail', pk=pk)
    else:
        form = SubmissionForm(instance=submission)

    return render(request, 'assignments/submit.html', {
        'assignment': assignment,
        'form': form,
        'submission': submission,
    })


@login_required
def grade_submission(request, submission_pk):
    submission = get_object_or_404(Submission, pk=submission_pk)
    assignment = submission.assignment

    if assignment.course.teacher != request.user and not request.user.is_staff:
        messages.error(request, 'Only teachers can grade submissions.')
        return redirect('assignments:detail', pk=assignment.pk)

    grade_obj, _ = AssignmentGrade.objects.get_or_create(submission=submission)

    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST, instance=grade_obj)
        if form.is_valid():
            g = form.save(commit=False)
            g.grader = request.user
            g.save()
            messages.success(request, 'Grade saved.')
            return redirect('assignments:submissions', pk=assignment.pk)
    else:
        form = GradeSubmissionForm(instance=grade_obj)

    return render(request, 'assignments/grade.html', {
        'submission': submission,
        'assignment': assignment,
        'form': form,
    })


class SubmissionListView(LoginRequiredMixin, ListView):
    template_name = 'assignments/submission_list.html'
    context_object_name = 'submissions'

    def get_queryset(self):
        assignment = get_object_or_404(Assignment, pk=self.kwargs['pk'])
        if assignment.course.teacher != self.request.user and not self.request.user.is_staff:
            return Submission.objects.none()
        return Submission.objects.filter(
            assignment=assignment, latest=True
        ).select_related('user').order_by('user__last_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = get_object_or_404(Assignment, pk=self.kwargs['pk'])
        return context


class AssignmentCreateView(TeacherRequiredMixin, CreateView):
    """Instructor: create an assignment for a course and add it as a course module."""
    model = Assignment
    form_class = AssignmentCreateForm
    template_name = 'assignments/assignment_create.html'

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=self.kwargs['course_pk'])
        if self.course.teacher != request.user and not request.user.is_staff:
            messages.error(request, 'You can only add assignments to your own courses.')
            return redirect('courses:detail', pk=self.course.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        section_pk = self.kwargs.get('section_pk')
        if section_pk:
            initial['section'] = section_pk
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = self.course
        return kwargs

    def form_valid(self, form):
        assignment = form.save(commit=False)
        assignment.course = self.course
        assignment.save()

        section = form.cleaned_data.get('section')
        CourseModule.objects.create(
            course=self.course,
            section=section,
            module_type=CourseModule.MODULE_ASSIGNMENT,
            instance_id=assignment.pk,
            name=assignment.name,
            visible=assignment.visible,
            sortorder=0,
        )
        messages.success(self.request, 'Assignment created and added to the course.')
        return redirect('courses:content', pk=self.course.pk)


class InstructorAssignmentListView(TeacherRequiredMixin, ListView):
    """Instructor: list assignments across courses they teach."""
    template_name = 'assignments/assignment_list_instructor.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        return (
            Assignment.objects.filter(course__teacher=self.request.user)
            .select_related('course')
            .order_by('-created_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_courses'] = Course.objects.filter(teacher=self.request.user).order_by('fullname')
        return context
