from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


User = get_user_model()

class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class")
    
    def __str__(self):
        return self.name


class UserSkill(models.Model):
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(SkillCategory, on_delete=models.CASCADE)
    level = models.CharField(max_length=15, choices=SKILL_LEVELS)
    can_teach = models.BooleanField(default=False)
    wants_to_learn = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'skill')
    
    def __str__(self):
        return f"{self.user.username} - {self.skill.name} ({self.level})"


class SkillExchange(models.Model):
    MEETING_TYPES = [
        ('virtual', 'Virtual Meeting'),
        ('in_person', 'In-Person Meeting'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]
    
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentoring_sessions')
    learner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_sessions')
    skill = models.ForeignKey(SkillCategory, on_delete=models.CASCADE)
    mentor_skill = models.ForeignKey(UserSkill, on_delete=models.CASCADE, related_name='mentor_skills')
    learner_skill = models.ForeignKey(UserSkill, on_delete=models.CASCADE, related_name='learner_skills')
    scheduled_time = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES, default='virtual')
    location = models.CharField(max_length=255, blank=True, null=True)  # Add this line
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    meeting_link = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.mentor.username} teaches {self.skill.name} to {self.learner.username}"


class Review(models.Model):
    RATING_CHOICES = [
        (1, '★☆☆☆☆'),
        (2, '★★☆☆☆'),
        (3, '★★★☆☆'),
        (4, '★★★★☆'),
        (5, '★★★★★'),
    ]
    
    exchange = models.OneToOneField(SkillExchange, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.reviewer.username} → {self.reviewed_user.username}: {self.rating} stars"


from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SkillRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    skill = models.ForeignKey('SkillCategory', on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester} → {self.receiver} for {self.skill}"

class CommunicationSession(models.Model):
    request = models.OneToOneField(SkillRequest, on_delete=models.CASCADE)
    room_id = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session for {self.request}"




