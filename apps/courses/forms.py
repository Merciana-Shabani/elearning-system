from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset
from .models import Course, CourseSection, CourseModule, CoursePage, CourseFile, CourseAnnouncement, Document


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'category', 'fullname', 'shortname', 'idnumber', 'summary', 'image',
            'format', 'enrollment_type', 'enrolment_key', 'max_students', 'price',
            'visible', 'startdate', 'enddate', 'completion_enabled', 'show_grades',
        ]
        widgets = {
            'startdate': forms.DateInput(attrs={'type': 'date'}),
            'enddate': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Basic Information',
                Row(Column('fullname', css_class='col-md-8'), Column('shortname', css_class='col-md-4')),
                Row(Column('category', css_class='col-md-6'), Column('idnumber', css_class='col-md-6')),
                'summary',
                'image',
            ),
            Fieldset('Enrollment & Pricing',
                Row(Column('enrollment_type', css_class='col-md-6'), Column('max_students', css_class='col-md-6')),
                Row(Column('enrolment_key', css_class='col-md-6'), Column('price', css_class='col-md-6')),
            ),
            Fieldset('Course Settings',
                Row(Column('format', css_class='col-md-4'), Column('startdate', css_class='col-md-4'), Column('enddate', css_class='col-md-4')),
                Row(Column('visible'), Column('completion_enabled'), Column('show_grades')),
            ),
            Submit('submit', 'Save Course', css_class='btn btn-primary mt-3'),
        )


class CourseSectionForm(forms.ModelForm):
    class Meta:
        model = CourseSection
        fields = ['name', 'summary', 'visible', 'required_section']

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course:
            qs = course.sections.all()
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            self.fields['required_section'].queryset = qs
            self.fields['required_section'].required = False


class CourseModuleForm(forms.ModelForm):
    """Form for adding/editing a course module. Requires course= in __init__."""
    class Meta:
        model = CourseModule
        fields = ['section', 'module_type', 'name', 'visible', 'sortorder', 'required_module']

    def __init__(self, *args, course=None, **kwargs):
        self.course = course
        super().__init__(*args, **kwargs)
        if course:
            self.fields['section'].queryset = course.sections.all()
            qs = CourseModule.objects.filter(course=course).exclude(pk=self.instance.pk if self.instance and self.instance.pk else 0)
            self.fields['required_module'].queryset = qs
            self.fields['required_module'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.course:
            instance.course = self.course
        if commit:
            instance.save()
        return instance


class CoursePageForm(forms.ModelForm):
    class Meta:
        model = CoursePage
        fields = ['name', 'intro', 'content', 'display']
        widgets = {
            'intro': forms.Textarea(attrs={'rows': 3}),
        }


class CourseFileForm(forms.ModelForm):
    class Meta:
        model = CourseFile
        fields = ['name', 'description', 'file', 'display']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class CourseAnnouncementForm(forms.ModelForm):
    class Meta:
        model = CourseAnnouncement
        fields = ['title', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4}),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'file', 'visible']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
