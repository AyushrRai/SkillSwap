from django import forms
from .models import MiniCourse, CourseModule, ModuleContent
from skills.models import SkillCategory

class MiniCourseForm(forms.ModelForm):
    skill = forms.ModelChoiceField(
        queryset=SkillCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = MiniCourse
        fields = ['title', 'description', 'skill', 'level', 'is_free', 'price', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class CourseModuleForm(forms.ModelForm):
    class Meta:
        model = CourseModule
        fields = ['title', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ModuleContentForm(forms.ModelForm):
    class Meta:
        model = ModuleContent
        fields = ['title', 'content_type', 'content', 'order', 'is_free_preview']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content_type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_free_preview': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }