from django import forms
from .models import SkillExchange, Review, UserSkill
from django.contrib.auth import get_user_model

User = get_user_model()


class SkillExchangeForm(forms.ModelForm):
    exchange_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    exchange_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        required=True
    )
    
    class Meta:
        model = SkillExchange
        fields = ['exchange_date', 'exchange_time', 'duration', 'meeting_type', 'location', 'notes']
        widgets = {
            'duration': forms.NumberInput(attrs={'min': 15, 'max': 240, 'step': 15}),
            'meeting_type': forms.RadioSelect(),
            'location': forms.TextInput(attrs={'placeholder': 'Enter meeting location'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional notes'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['meeting_type'].widget.choices = SkillExchange.MEETING_TYPES
    
    def clean(self):
        cleaned_data = super().clean()
        exchange_date = cleaned_data.get('exchange_date')
        exchange_time = cleaned_data.get('exchange_time')
        
        if exchange_date and exchange_date < timezone.now().date():
            raise forms.ValidationError("Exchange date cannot be in the past")
            
        return cleaned_data

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, '★' * i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }



from django import forms
from .models import SkillRequest

class SkillRequestForm(forms.ModelForm):
    class Meta:
        model = SkillRequest
        fields = ['skill', 'message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Explain why you want to learn this skill...'
            }),
        }