# models.py
from django.db import models
from django.contrib.auth import get_user_model
from skills.models import SkillCategory
from django.utils import timezone

User = get_user_model()

class SkillCircle(models.Model):
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('hidden', 'Hidden'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    skill = models.ForeignKey(SkillCategory, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_skill_circles')
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)
    cover_image = models.ImageField(upload_to='circle_covers/', blank=True)
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public')
    rules = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    is_active = models.BooleanField(default=True)
    member_limit = models.PositiveIntegerField(default=0, help_text="0 means no limit")
    
    def __str__(self):
        return self.name
    
    def get_tags(self):
        return [tag.strip() for tag in self.tags.split(',')] if self.tags else []
    
    def member_count(self):
        return self.circlemembership_set.count()
    
    def is_full(self):
        return self.member_limit > 0 and self.member_count() >= self.member_limit

class CircleMembership(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('banned', 'Banned'),
    ]
    
    circle = models.ForeignKey(SkillCircle, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='approved')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)
    is_favorite = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('circle', 'user')
        ordering = ['-is_favorite', '-joined_at']
    
    def __str__(self):
        return f"{self.user.username} in {self.circle.name} ({self.role})"

class CirclePost(models.Model):
    POST_TYPES = [
        ('discussion', 'Discussion'),
        ('question', 'Question'),
        ('resource', 'Resource'),
        ('announcement', 'Announcement'),
    ]
    
    circle = models.ForeignKey(SkillCircle, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    post_type = models.CharField(max_length=12, choices=POST_TYPES, default='discussion')
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"Post by {self.author.username} in {self.circle.name}"
    
    def like_count(self):
        return self.postlike_set.count()
    
    def comment_count(self):
        return self.postcomment_set.count()

class PostLike(models.Model):
    post = models.ForeignKey(CirclePost, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'user')
    
    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"

class PostComment(models.Model):
    post = models.ForeignKey(CirclePost, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post.id}"

class CircleEvent(models.Model):
    EVENT_TYPES = [
        ('workshop', 'Workshop'),
        ('meetup', 'Meetup'),
        ('webinar', 'Webinar'),
        ('challenge', 'Challenge'),
    ]
    
    circle = models.ForeignKey(SkillCircle, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    meeting_link = models.URLField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES, default='meetup')
    max_participants = models.PositiveIntegerField(default=0, help_text="0 means no limit")
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} in {self.circle.name}"
    
    def is_upcoming(self):
        return self.start_time > timezone.now()
    
    def participant_count(self):
        return self.eventregistration_set.count()

class EventRegistration(models.Model):
    event = models.ForeignKey(CircleEvent, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('event', 'user')
    
    def __str__(self):
        return f"{self.user.username} registered for {self.event.title}"

class CircleResource(models.Model):
    RESOURCE_TYPES = [
        ('document', 'Document'),
        ('link', 'Link'),
        ('video', 'Video'),
        ('book', 'Book'),
    ]
    
    circle = models.ForeignKey(SkillCircle, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    file = models.FileField(upload_to='circle_resources/', blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} in {self.circle.name}"

class CircleInvitation(models.Model):
    circle = models.ForeignKey(SkillCircle, on_delete=models.CASCADE)
    email = models.EmailField()
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=100, unique=True)
    accepted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Invitation to {self.circle.name} for {self.email}"

class CircleNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_post', 'New Post'),
        ('event_reminder', 'Event Reminder'),
        ('membership_request', 'Membership Request'),
        ('membership_approved', 'Membership Approved'),
        ('mention', 'Mention'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    circle = models.ForeignKey(SkillCircle, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)
    related_post = models.ForeignKey(CirclePost, on_delete=models.CASCADE, null=True, blank=True)
    related_event = models.ForeignKey(CircleEvent, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"


from django.db import models

class Circle(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
