# forms.py
from django import forms
from .models import (
    SkillCircle, CirclePost, CircleEvent, 
    CircleResource, CircleInvitation, PostComment
)
from django.utils import timezone
from datetime import timedelta
from .models import SkillCategory


class SkillCircleForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'comma,separated,tags',
            'class': 'form-control'
        }),
        help_text="Add relevant tags separated by commas"
    )
    
    class Meta:
        model = SkillCircle
        fields = [
            'name', 'description', 'skill', 
            'cover_image', 'privacy', 'rules',
            'tags', 'member_limit'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'rules': forms.Textarea(attrs={'rows': 3}),
        }

class CirclePostForm(forms.ModelForm):
    class Meta:
        model = CirclePost
        fields = ['content', 'post_type']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your thoughts, ask a question, or post a resource...'
            }),
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = CircleEvent
        fields = [
            'title', 'description', 'start_time', 
            'end_time', 'meeting_link', 'event_type',
            'max_participants', 'is_recurring', 'recurrence_pattern'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_time'].input_formats = ['%Y-%m-%dT%H:%M']

class ResourceForm(forms.ModelForm):
    class Meta:
        model = CircleResource
        fields = ['title', 'description', 'resource_type', 'file', 'url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        file = cleaned_data.get('file')
        url = cleaned_data.get('url')
        
        if resource_type == 'link' and not url:
            raise forms.ValidationError("URL is required for link resources")
        if resource_type != 'link' and not file:
            raise forms.ValidationError("File upload is required for this resource type")
        
        return cleaned_data

class InvitationForm(forms.ModelForm):
    class Meta:
        model = CircleInvitation
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter email address to invite'
            })
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = PostComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Write your comment...',
                'class': 'form-control'
            })
        }

class MembershipRequestForm(forms.Form):
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Optional message to circle admins...'
        })
    )

class CircleSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search circles...',
            'class': 'form-control'
        })
    )
    skill = forms.ModelChoiceField(
        queryset=SkillCategory.objects.all(),
        required=False,
        empty_label="All Skills"
    )
    privacy = forms.ChoiceField(
        choices=[('', 'All')] + SkillCircle.PRIVACY_CHOICES,
        required=False
    )