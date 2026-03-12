from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Quiz, QuizAttempt, Question, QuestionResponse, Answer
from .forms import QuizCreateForm, QuestionForm, AnswerForm
from apps.enrollment.models import Enrollment
from apps.courses.models import Course, CourseModule
from apps.users.mixins import TeacherRequiredMixin


class QuizListView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = 'quizzes/quiz_list.html'
    context_object_name = 'quizzes'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        qs = Quiz.objects.filter(visible=True).select_related('course', 'course__teacher').order_by('-created_at')
        enrolled_course_ids = set(
            Enrollment.objects.filter(user=user, status='active').values_list('course_id', flat=True)
        )
        if user.is_staff:
            return qs
        if user.is_instructor:
            return qs.filter(course__teacher=user)
        # Students: only show quizzes that are currently open
        now = timezone.now()
        return qs.filter(
            course_id__in=enrolled_course_ids
        ).filter(
            Q(time_open__isnull=True) | Q(time_open__lte=now),
            Q(time_close__isnull=True) | Q(time_close__gte=now),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_instructor or user.is_staff:
            context['my_courses'] = Course.objects.filter(teacher=user).order_by('fullname')
        else:
            context['my_courses'] = []
        return context


class QuizDetailView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'quizzes/quiz_detail.html'
    context_object_name = 'quiz'

    def dispatch(self, request, *args, **kwargs):
        quiz = self.get_object()
        is_teacher = quiz.course.teacher == request.user or request.user.is_staff
        if not is_teacher:
            now = timezone.now()
            is_open = (
                (quiz.time_open is None or now >= quiz.time_open) and
                (quiz.time_close is None or now <= quiz.time_close)
            )
            if not is_open:
                messages.warning(request, 'This quiz is not open yet.')
                return redirect('courses:content', pk=quiz.course.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()
        user = self.request.user
        context['attempts'] = QuizAttempt.objects.filter(
            quiz=quiz, user=user
        ).order_by('-time_start')
        context['attempt_count'] = context['attempts'].count()
        context['can_attempt'] = (
            quiz.attempts_allowed == -1 or
            context['attempt_count'] < quiz.attempts_allowed
        )
        context['is_teacher'] = (
            quiz.course.teacher == user or user.is_staff
        )
        if context['is_teacher']:
            context['questions'] = quiz.questions.prefetch_related('answers').order_by('sortorder')
        # Check if quiz is open
        now = timezone.now()
        context['is_open'] = (
            (quiz.time_open is None or now >= quiz.time_open) and
            (quiz.time_close is None or now <= quiz.time_close)
        )
        return context


class QuizCreateView(TeacherRequiredMixin, CreateView):
    """Instructor: create a quiz for a course and add it as a course module."""
    model = Quiz
    form_class = QuizCreateForm
    template_name = 'quizzes/quiz_create.html'

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=self.kwargs['course_pk'])
        if self.course.teacher != request.user and not request.user.is_staff:
            messages.error(request, 'You can only add quizzes to your own courses.')
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
        quiz = form.save(commit=False)
        quiz.course = self.course
        quiz.save()

        section = form.cleaned_data.get('section')
        CourseModule.objects.create(
            course=self.course,
            section=section,
            module_type=CourseModule.MODULE_QUIZ,
            instance_id=quiz.pk,
            name=quiz.name,
            visible=quiz.visible,
            sortorder=0,
        )
        messages.success(self.request, 'Quiz created and added to the course.')
        return redirect('courses:content', pk=self.course.pk)


class QuizUpdateView(TeacherRequiredMixin, UpdateView):
    """Instructor: edit quiz settings and update the course module link."""
    model = Quiz
    form_class = QuizCreateForm
    template_name = 'quizzes/quiz_edit.html'
    context_object_name = 'quiz'

    def dispatch(self, request, *args, **kwargs):
        quiz = self.get_object()
        if quiz.course.teacher != request.user and not request.user.is_staff:
            messages.error(request, 'You can only edit quizzes in your own courses.')
            return redirect('quizzes:detail', pk=quiz.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course'] = self.object.course
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        mod = CourseModule.objects.filter(
            course=self.object.course,
            module_type=CourseModule.MODULE_QUIZ,
            instance_id=self.object.pk,
        ).first()
        if mod and mod.section_id:
            initial['section'] = mod.section_id
        return initial

    def form_valid(self, form):
        form.save()
        mod = CourseModule.objects.filter(
            course=self.object.course,
            module_type=CourseModule.MODULE_QUIZ,
            instance_id=self.object.pk,
        ).first()
        if mod:
            mod.section = form.cleaned_data.get('section') or mod.section
            mod.name = self.object.name
            mod.visible = self.object.visible
            mod.save()
        messages.success(self.request, 'Quiz updated.')
        return redirect('quizzes:detail', pk=self.object.pk)


class QuestionCreateView(TeacherRequiredMixin, CreateView):
    """Instructor: add a question to a quiz (then add answers so quiz can be marked automatically)."""
    model = Question
    form_class = QuestionForm
    template_name = 'quizzes/question_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_pk'])
        if self.quiz.course.teacher != request.user and not request.user.is_staff:
            messages.error(request, 'You can only edit quizzes in your own courses.')
            return redirect('quizzes:detail', pk=self.quiz.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.quiz = self.quiz
        form.instance.sortorder = self.quiz.questions.count()
        messages.success(self.request, 'Question added. Add answer options (with Correct/Wrong) so the quiz can be marked automatically.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('quizzes:detail', kwargs={'pk': self.quiz.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.quiz
        return context


class QuestionUpdateView(TeacherRequiredMixin, UpdateView):
    """Instructor: edit a question."""
    model = Question
    form_class = QuestionForm
    template_name = 'quizzes/question_form.html'
    context_object_name = 'question'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.quiz.course.teacher != request.user and not request.user.is_staff:
            messages.error(request, 'You can only edit questions in your own courses.')
            return redirect('quizzes:detail', pk=obj.quiz.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('quizzes:detail', kwargs={'pk': self.object.quiz.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quiz'] = self.object.quiz
        return context


class AnswerCreateView(TeacherRequiredMixin, CreateView):
    """Instructor: add an answer option (fraction=1 for correct so quiz is marked automatically)."""
    model = Answer
    form_class = AnswerForm
    template_name = 'quizzes/answer_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
        if self.question.quiz.course.teacher != request.user and not request.user.is_staff:
            messages.error(request, 'You can only edit questions in your own courses.')
            return redirect('quizzes:detail', pk=self.question.quiz.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.question = self.question
        form.instance.sortorder = self.question.answers.count()
        messages.success(self.request, 'Answer added. Set "Correct" for the right option(s) so the quiz can be marked automatically.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('quizzes:detail', kwargs={'pk': self.question.quiz.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.question
        context['quiz'] = self.question.quiz
        return context


@login_required
def start_attempt(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, visible=True)

    is_teacher = quiz.course.teacher == request.user or request.user.is_staff
    if not is_teacher and not Enrollment.objects.filter(
        user=request.user, course=quiz.course, status='active'
    ).exists():
        messages.error(request, 'You must be enrolled to take this quiz.')
        return redirect('courses:detail', pk=quiz.course.pk)

    now = timezone.now()
    if quiz.time_open and now < quiz.time_open:
        messages.error(request, 'This quiz is not yet open.')
        return redirect('quizzes:detail', pk=pk)
    if quiz.time_close and now > quiz.time_close:
        messages.error(request, 'This quiz has closed.')
        return redirect('quizzes:detail', pk=pk)

    attempt_count = QuizAttempt.objects.filter(quiz=quiz, user=request.user).count()
    if quiz.attempts_allowed != -1 and attempt_count >= quiz.attempts_allowed:
        messages.error(request, 'You have used all your allowed attempts.')
        return redirect('quizzes:detail', pk=pk)

    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        user=request.user,
        attempt_number=attempt_count + 1,
        state=QuizAttempt.STATE_IN_PROGRESS,
    )
    return redirect('quizzes:attempt', attempt_pk=attempt.pk)


@login_required
def take_attempt(request, attempt_pk):
    attempt = get_object_or_404(
        QuizAttempt, pk=attempt_pk, user=request.user, state=QuizAttempt.STATE_IN_PROGRESS
    )
    quiz = attempt.quiz
    questions = quiz.questions.prefetch_related('answers').order_by('sortorder')

    now = timezone.now()
    time_limit_exceeded = False
    if quiz.time_limit > 0:
        elapsed = (now - attempt.time_start).total_seconds()
        if elapsed >= quiz.time_limit:
            time_limit_exceeded = True
    quiz_closed = quiz.time_close and now > quiz.time_close

    # Mark after limit time ends: auto-submit, grade, and show result
    if time_limit_exceeded or quiz_closed:
        if request.method == 'POST':
            _save_responses(request, attempt, questions)
        _grade_attempt(attempt, questions)
        attempt.state = QuizAttempt.STATE_FINISHED
        attempt.time_finish = now
        attempt.save()
        if time_limit_exceeded:
            messages.warning(request, 'Time limit ended. Your answers were submitted and marked.')
        else:
            messages.info(request, 'Quiz has closed. Your answers were submitted and marked.')
        return redirect('quizzes:result', attempt_pk=attempt.pk)

    if request.method == 'POST':
        if 'finish' in request.POST:
            _save_responses(request, attempt, questions)
            _grade_attempt(attempt, questions)
            attempt.state = QuizAttempt.STATE_FINISHED
            attempt.time_finish = timezone.now()
            attempt.save()
            messages.success(request, 'Quiz submitted successfully.')
            return redirect('quizzes:result', attempt_pk=attempt.pk)
        else:
            _save_responses(request, attempt, questions)
            messages.success(request, 'Progress saved.')

    responses = {r.question_id: r for r in attempt.responses.prefetch_related('selected_answers')}
    time_remaining = None
    if quiz.time_limit > 0:
        elapsed = (timezone.now() - attempt.time_start).total_seconds()
        time_remaining = max(0, quiz.time_limit - elapsed)

    return render(request, 'quizzes/take_quiz.html', {
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
        'responses': responses,
        'time_remaining': time_remaining,
    })


def _written_answer_to_choice(question, text):
    """Map student's written answer (e.g. '1', 'A', or option text) to an Answer, or None."""
    if not text or not text.strip():
        return None
    text = text.strip()
    answers = list(question.answers.order_by('sortorder'))
    if not answers:
        return None
    # By number: 1, 2, 3, ...
    if text.isdigit():
        idx = int(text)
        if 1 <= idx <= len(answers):
            return answers[idx - 1]
    # By letter: A, a, B, b, ...
    if len(text) == 1:
        upper = text.upper()
        if 'A' <= upper <= 'Z':
            idx = ord(upper) - ord('A')
            if idx < len(answers):
                return answers[idx]
    # By matching option text (case-insensitive)
    text_lower = text.lower()
    for answer in answers:
        if text_lower in (answer.answer_text or '').lower():
            return answer
        if (answer.answer_text or '').strip().lower() in text_lower:
            return answer
    return None


def _save_responses(request, attempt, questions):
    for question in questions:
        response, _ = QuestionResponse.objects.get_or_create(
            attempt=attempt, question=question
        )
        if question.question_type in [Question.QTYPE_ESSAY, Question.QTYPE_SHORTANSWER]:
            response.text_response = request.POST.get(f'q_{question.pk}', '')
            response.save()
        else:
            # Multiple choice / truefalse: student writes answer in a text box
            raw = request.POST.get(f'q_{question.pk}', '').strip()
            response.text_response = raw
            chosen = _written_answer_to_choice(question, raw)
            if chosen:
                response.selected_answers.set([chosen])
            else:
                response.selected_answers.clear()
            response.save()


def _grade_attempt(attempt, questions):
    total = 0
    for question in questions:
        try:
            response = attempt.responses.get(question=question)
        except QuestionResponse.DoesNotExist:
            continue

        if question.question_type == Question.QTYPE_ESSAY:
            continue  # Manual grading needed

        correct_fractions = sum(
            float(a.fraction) for a in response.selected_answers.all()
        )
        earned = max(0, correct_fractions) * float(question.default_mark)
        response.fraction = earned / float(question.default_mark) if question.default_mark else 0
        response.save()
        total += earned

    attempt.sumgrades = total
    attempt.save()


@login_required
def view_result(request, attempt_pk):
    attempt = get_object_or_404(
        QuizAttempt, pk=attempt_pk,
        user=request.user,
        state=QuizAttempt.STATE_FINISHED
    )
    questions = attempt.quiz.questions.prefetch_related('answers', 'responses').order_by('sortorder')
    responses = {r.question_id: r for r in attempt.responses.prefetch_related('selected_answers')}

    return render(request, 'quizzes/result.html', {
        'attempt': attempt,
        'questions': questions,
        'responses': responses,
    })
