from django import forms
from django.utils import timezone as tz
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from apps.courses.models import CourseSection
from .models import Quiz, Question, Answer


class QuizCreateForm(forms.ModelForm):
    """Instructor: create a quiz for a course (requires open/close times) and pick a section to place it in."""
    section = forms.ModelChoiceField(queryset=CourseSection.objects.none(), required=False)

    class Meta:
        model = Quiz
        fields = ['section', 'name', 'intro', 'time_open', 'time_close', 'time_limit', 'attempts_allowed', 'visible']
        widgets = {
            'time_open': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'time_close': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course is not None:
            self.fields['section'].queryset = course.sections.all()

        # Require start/end times (business rule)
        self.fields['time_open'].required = True
        self.fields['time_close'].required = True
        # Accept browser datetime-local format
        for fname in ('time_open', 'time_close'):
            self.fields[fname].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S']

        submit_label = 'Save changes' if (self.instance and self.instance.pk) else 'Create quiz'
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Quiz',
                Row(
                    Column('section', css_class='col-md-6'),
                    Column('name', css_class='col-md-6'),
                ),
                'intro',
            ),
            Fieldset(
                'Availability',
                Row(
                    Column('time_open', css_class='col-md-6'),
                    Column('time_close', css_class='col-md-6'),
                ),
                Row(
                    Column('time_limit', css_class='col-md-4'),
                    Column('attempts_allowed', css_class='col-md-4'),
                    Column('visible', css_class='col-md-4'),
                ),
            ),
            Submit('submit', submit_label, css_class='btn btn-primary mt-3'),
        )

    def clean_time_open(self):
        value = self.cleaned_data.get('time_open')
        if value and tz.is_naive(value):
            # Always interpret as site timezone (TIME_ZONE) so "15:00" = 15:00 local
            value = tz.make_aware(value, tz.get_default_timezone())
        return value

    def clean_time_close(self):
        value = self.cleaned_data.get('time_close')
        if value and tz.is_naive(value):
            value = tz.make_aware(value, tz.get_default_timezone())
        return value

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('time_open')
        end = cleaned.get('time_close')
        if start and end and end <= start:
            self.add_error('time_close', 'End time must be after start time.')
        return cleaned


class QuestionForm(forms.ModelForm):
    """Instructor: add or edit a quiz question."""
    class Meta:
        model = Question
        fields = ['name', 'question_type', 'question_text', 'default_mark', 'sortorder']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Question', 'name', 'question_type', 'question_text', Row(Column('default_mark', css_class='col-md-6'), Column('sortorder', css_class='col-md-6'))),
            Submit('submit', 'Save question', css_class='btn btn-primary mt-3'),
        )


class AnswerForm(forms.ModelForm):
    """Instructor: add an answer option (set fraction=1 for correct so quiz can be marked automatically)."""
    class Meta:
        model = Answer
        fields = ['answer_text', 'fraction', 'sortorder']
        widgets = {
            'answer_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Answer text'}),
            'fraction': forms.Select(choices=[(0, 'Wrong (0)'), (1, 'Correct (1)')]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fraction'].initial = 0
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('answer_text', css_class='col-md-8'), Column('fraction', css_class='col-md-2'), Column('sortorder', css_class='col-md-2')),
            Submit('submit', 'Add answer', css_class='btn btn-primary mt-2'),
        )

