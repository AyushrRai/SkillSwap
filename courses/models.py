from django.db import models
from django.contrib.auth import get_user_model
from skills.models import SkillCategory

User = get_user_model()

class MiniCourse(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    skill = models.ForeignKey(SkillCategory, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_courses')
    level = models.CharField(max_length=15, choices=LEVEL_CHOICES)
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True)
    
    def __str__(self):
        return self.title

class CourseModule(models.Model):
    course = models.ForeignKey(MiniCourse, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class ModuleContent(models.Model):
    CONTENT_TYPES = [
        ('video', 'Video'),
        ('article', 'Article'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    ]
    
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    content = models.TextField()  # Can be video URL, article text, etc.
    order = models.PositiveIntegerField(default=0)
    is_free_preview = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"

class CourseEnrollment(models.Model):
    course = models.ForeignKey(MiniCourse, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('course', 'user')
    
    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"