from django.contrib import admin
from .models import Quiz, Question, Answer, QuizAttempt, QuestionResponse


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ['answer_text', 'fraction', 'feedback', 'sortorder']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['name', 'question_type', 'default_mark', 'sortorder']
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'question_count', 'grade', 'attempts_allowed',
                    'time_open', 'time_close', 'visible']
    list_filter = ['visible', 'course', 'grade_method']
    search_fields = ['name', 'course__fullname']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['name', 'quiz', 'question_type', 'default_mark', 'sortorder']
    list_filter = ['question_type', 'quiz__course']
    search_fields = ['name', 'question_text']
    inlines = [AnswerInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'attempt_number', 'state', 'sumgrades',
                    'time_start', 'time_finish']
    list_filter = ['state', 'quiz__course']
    search_fields = ['user__email', 'quiz__name']
    readonly_fields = ['time_start', 'time_modified']
