from django.contrib import admin
from .models import Assignment, Submission, AssignmentGrade


class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0
    readonly_fields = ['user', 'status', 'submitted_at', 'modified_at']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'submission_type', 'grading_method', 'max_grade', 'due_date', 'visible']
    list_filter = ['submission_type', 'grading_method', 'visible', 'course']
    search_fields = ['name', 'course__fullname']
    inlines = [SubmissionInline]
    fieldsets = (
        (None, {'fields': ('course', 'name', 'intro', 'rubric_criteria')}),
        ('Submission', {'fields': ('submission_type', 'allow_submissions_from', 'due_date', 'cut_off_date', 'max_attempts', 'max_files', 'allowed_file_types')}),
        ('Grading', {'fields': ('grading_method', 'max_grade', 'passing_grade')}),
        (None, {'fields': ('visible',)}),
    )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'assignment', 'status', 'submitted_at']
    list_filter = ['status', 'assignment__course']
    search_fields = ['user__email', 'assignment__name']


@admin.register(AssignmentGrade)
class AssignmentGradeAdmin(admin.ModelAdmin):
    list_display = ['submission', 'grader', 'grade', 'graded_at', 'released']
    list_filter = ['released']
