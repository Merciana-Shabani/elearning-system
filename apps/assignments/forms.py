from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from apps.courses.models import CourseSection
from .models import Submission, AssignmentGrade, Assignment


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['online_text', 'file']


class GradeSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentGrade
        fields = ['grade', 'feedback', 'released']
        widgets = {
            'grade': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


class AssignmentCreateForm(forms.ModelForm):
    """Instructor: create an assignment for a course, and optionally pick a section to place it in."""
    section = forms.ModelChoiceField(queryset=CourseSection.objects.none(), required=False)

    class Meta:
        model = Assignment
        fields = ['section', 'name', 'intro', 'due_date', 'cut_off_date', 'visible']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'cut_off_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course is not None:
            self.fields['section'].queryset = course.sections.all()

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Assignment',
                Row(
                    Column('section', css_class='col-md-6'),
                    Column('name', css_class='col-md-6'),
                ),
                'intro',
            ),
            Fieldset(
                'Schedule',
                Row(
                    Column('due_date', css_class='col-md-6'),
                    Column('cut_off_date', css_class='col-md-6'),
                ),
                'visible',
            ),
            Submit('submit', 'Create assignment', css_class='btn btn-primary mt-3'),
        )
