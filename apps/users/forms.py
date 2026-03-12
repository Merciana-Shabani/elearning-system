from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from allauth.account.forms import SignupForm
from .models import User, UserProfile


class CustomSignupForm(SignupForm):
    """
    Signup form that sets user category:
    - Student (DPA / Normal Staff)
    - Instructor
    - Moderator
    """
    role = forms.ChoiceField(
        choices=[
            (User.ROLE_STUDENT, 'Student'),
            (User.ROLE_TEACHER, 'Instructor'),
            (User.ROLE_MODERATOR, 'Moderator'),
        ],
        widget=forms.HiddenInput,
        required=False,
    )
    student_type = forms.ChoiceField(
        choices=User.STUDENT_TYPE_CHOICES,
        widget=forms.HiddenInput,
        required=False,
    )
    staff_code = forms.CharField(
        label='Staff code',
        max_length=64,
        required=False,
        strip=True,
        help_text='Required for Instructors/Moderators. Use your official staff/service number.',
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request')
        super().__init__(*args, **kwargs)
        role = None
        student_type = None
        if self.request:
            role = self.request.session.get('signup_role')
            student_type = self.request.session.get('signup_student_type')
        self.fields['role'].initial = role or User.ROLE_STUDENT
        self.fields['student_type'].initial = student_type or User.STUDENT_DPA

    def clean_role(self):
        role = (self.request.session.get('signup_role') if self.request else None) or self.cleaned_data.get('role')
        allowed = {User.ROLE_STUDENT, User.ROLE_TEACHER, User.ROLE_MODERATOR}
        return role if role in allowed else User.ROLE_STUDENT

    def clean_student_type(self):
        role = self.clean_role()
        student_type = (self.request.session.get('signup_student_type') if self.request else None) or self.cleaned_data.get('student_type')
        if role != User.ROLE_STUDENT:
            return ''
        allowed = {User.STUDENT_DPA, User.STUDENT_NORMAL_STAFF}
        return student_type if student_type in allowed else User.STUDENT_DPA

    def clean_staff_code(self):
        role = self.clean_role()
        staff_code = (self.cleaned_data.get('staff_code') or '').strip()
        if role in {User.ROLE_TEACHER, User.ROLE_MODERATOR}:
            if not staff_code:
                raise forms.ValidationError('Staff code is required for Instructor/Moderator accounts.')
            if User.objects.filter(staff_code=staff_code).exists():
                raise forms.ValidationError('This staff code is already registered.')
            return staff_code
        return None

    def save(self, request):
        user = super().save(request)
        user.role = self.cleaned_data.get('role') or User.ROLE_STUDENT
        user.student_type = self.cleaned_data.get('student_type') or ''
        user.staff_code = self.cleaned_data.get('staff_code') or None
        user.save(update_fields=['role', 'student_type', 'staff_code'])
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'bio', 'avatar',
                  'phone', 'city', 'country', 'timezone', 'lang',
                  'department', 'institution', 'url']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
            ),
            Row(
                Column('username', css_class='col-md-6'),
                Column('lang', css_class='col-md-6'),
            ),
            'bio',
            'avatar',
            Row(
                Column('phone', css_class='col-md-6'),
                Column('city', css_class='col-md-6'),
            ),
            Row(
                Column('country', css_class='col-md-6'),
                Column('timezone', css_class='col-md-6'),
            ),
            Row(
                Column('department', css_class='col-md-6'),
                Column('institution', css_class='col-md-6'),
            ),
            'url',
            Submit('submit', 'Save Profile', css_class='btn btn-primary'),
        )


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['website', 'interests', 'linkedin', 'twitter', 'skype']
        widgets = {
            'interests': forms.Textarea(attrs={'rows': 3}),
        }
