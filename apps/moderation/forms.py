from django import forms
from django.utils import timezone

from .models import InstructorRoleApplication, ModerationAction, ContentReport


class InstructorApplicationDecisionForm(forms.Form):
    decision_reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), required=False)


class RejectInstructorApplicationForm(forms.Form):
    decision_reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), required=True)


class ModerationActionForm(forms.Form):
    action_type = forms.ChoiceField(choices=ModerationAction.ACTION_CHOICES)
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=True)
    suspend_days = forms.IntegerField(required=False, min_value=1, max_value=365)

    def clean(self):
        data = super().clean()
        action_type = data.get("action_type")
        days = data.get("suspend_days")
        if action_type == ModerationAction.ACTION_SUSPEND and not days:
            self.add_error("suspend_days", "Required for suspensions.")
        return data

    def build_expires_at(self):
        days = self.cleaned_data.get("suspend_days")
        if not days:
            return None
        return timezone.now() + timezone.timedelta(days=days)


class ReportResolveForm(forms.Form):
    resolution_notes = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)
    action = forms.ChoiceField(
        choices=[
            ("close", "Close report (no content change)"),
            ("hide", "Hide content"),
            ("remove", "Remove content"),
        ]
    )

