from django.db import models
from django.conf import settings
from ckeditor_uploader.fields import RichTextUploadingField
import json


class Quiz(models.Model):
    """
    Quiz activity.
    Mirrors Moodle's mdl_quiz table.
    """
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE, related_name='quizzes'
    )
    name = models.CharField(max_length=255)
    intro = RichTextUploadingField(blank=True, verbose_name='Instructions')
    time_open = models.DateTimeField(null=True, blank=True, help_text='Quiz opens at')
    time_close = models.DateTimeField(null=True, blank=True, help_text='Quiz closes at')
    time_limit = models.IntegerField(default=0, help_text='Time limit in seconds, 0=unlimited')
    grade = models.DecimalField(max_digits=6, decimal_places=2, default=10)
    attempts_allowed = models.IntegerField(default=1, help_text='-1 = unlimited')
    grade_method = models.IntegerField(
        default=1,
        choices=[(1, 'Highest grade'), (2, 'Average grade'), (3, 'First attempt'), (4, 'Last attempt')]
    )
    shuffle_questions = models.BooleanField(default=False)
    shuffle_answers = models.BooleanField(default=True)
    questions_per_page = models.IntegerField(default=0, help_text='0 = all on one page')
    show_user_picture = models.BooleanField(default=False)
    decimal_points = models.IntegerField(default=2)
    show_blocks = models.BooleanField(default=False)
    pass_grade = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_quizzes'
        verbose_name_plural = 'Quizzes'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.course.shortname})'

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    """
    Quiz question.
    Mirrors Moodle's mdl_question table.
    """
    QTYPE_MULTICHOICE = 'multichoice'
    QTYPE_TRUEFALSE = 'truefalse'
    QTYPE_SHORTANSWER = 'shortanswer'
    QTYPE_NUMERICAL = 'numerical'
    QTYPE_ESSAY = 'essay'
    QTYPE_MATCHING = 'matching'
    QTYPE_DDWTOS = 'ddwtos'

    QTYPE_CHOICES = [
        (QTYPE_MULTICHOICE, 'Multiple Choice'),
        (QTYPE_TRUEFALSE, 'True/False'),
        (QTYPE_SHORTANSWER, 'Short Answer'),
        (QTYPE_NUMERICAL, 'Numerical'),
        (QTYPE_ESSAY, 'Essay'),
        (QTYPE_MATCHING, 'Matching'),
        (QTYPE_DDWTOS, 'Drag and drop into text'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QTYPE_CHOICES, default=QTYPE_MULTICHOICE)
    name = models.CharField(max_length=255)
    question_text = RichTextUploadingField()
    general_feedback = RichTextUploadingField(blank=True)
    default_mark = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    penalty = models.DecimalField(
        max_digits=6, decimal_places=2, default=0.3333333,
        help_text='Fraction deducted per wrong attempt (for multiple tries)'
    )
    sortorder = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_questions'
        ordering = ['sortorder', 'id']

    def __str__(self):
        return self.name


class Answer(models.Model):
    """Answer option for a question."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    fraction = models.DecimalField(
        max_digits=6, decimal_places=5, default=0,
        help_text='1.0 = correct, 0.0 = wrong, negative for penalty'
    )
    feedback = models.TextField(blank=True)
    sortorder = models.IntegerField(default=0)

    class Meta:
        db_table = 'elening_answers'
        ordering = ['sortorder']

    def __str__(self):
        return f'{self.answer_text[:50]} (fraction: {self.fraction})'

    @property
    def is_correct(self):
        return self.fraction > 0


class QuizAttempt(models.Model):
    """
    A student's attempt at a quiz.
    Mirrors Moodle's mdl_quiz_attempts.
    """
    STATE_IN_PROGRESS = 'inprogress'
    STATE_OVERDUE = 'overdue'
    STATE_FINISHED = 'finished'
    STATE_ABANDONED = 'abandoned'

    STATE_CHOICES = [
        (STATE_IN_PROGRESS, 'In Progress'),
        (STATE_OVERDUE, 'Overdue'),
        (STATE_FINISHED, 'Finished'),
        (STATE_ABANDONED, 'Abandoned'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts'
    )
    attempt_number = models.IntegerField(default=1)
    state = models.CharField(max_length=16, choices=STATE_CHOICES, default=STATE_IN_PROGRESS)
    time_start = models.DateTimeField(auto_now_add=True)
    time_finish = models.DateTimeField(null=True, blank=True)
    time_modified = models.DateTimeField(auto_now=True)
    sumgrades = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    layout = models.TextField(blank=True, help_text='Comma-separated question IDs in page order')
    current_page = models.IntegerField(default=0)
    preview = models.BooleanField(default=False)

    class Meta:
        db_table = 'elening_quiz_attempts'
        unique_together = ('quiz', 'user', 'attempt_number')
        ordering = ['-time_start']

    def __str__(self):
        return f'{self.user} attempt #{self.attempt_number} on {self.quiz}'

    @property
    def score_percentage(self):
        if self.sumgrades is None or self.quiz.grade == 0:
            return 0
        return round((float(self.sumgrades) / float(self.quiz.grade)) * 100, 1)

    @property
    def passed(self):
        if self.quiz.pass_grade == 0:
            return None
        return self.sumgrades >= self.quiz.pass_grade


class QuestionResponse(models.Model):
    """Student's response to a question in an attempt."""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    selected_answers = models.ManyToManyField(Answer, blank=True)
    text_response = models.TextField(blank=True)
    fraction = models.DecimalField(max_digits=6, decimal_places=5, default=0)
    flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elening_question_responses'
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f'{self.attempt} → Q{self.question.id}'
