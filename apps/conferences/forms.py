from django import forms
from .models import ConferenceRoom


class ConferenceRoomForm(forms.ModelForm):
    class Meta:
        model = ConferenceRoom
        fields = [
            'title', 'description', 'course',
            'scheduled_at', 'duration_minutes', 'max_participants',
            'require_password', 'room_password',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'scheduled_at': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scheduled_at'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['course'].required = False
        self.fields['course'].empty_label = '— No specific course —'
        self.fields['scheduled_at'].required = False
        self.fields['duration_minutes'].required = False
        self.fields['duration_minutes'].initial = 120
        self.fields['room_password'].required = False
