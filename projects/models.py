
from django.db import models
from django.contrib.auth import get_user_model
from skills.models import SkillCategory


User = get_user_model()

class Project(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    required_skills = models.ManyToManyField(SkillCategory)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='planning')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_open = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class ProjectTeam(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('lead', 'Lead'),
        ('contributor', 'Contributor'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    contribution = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('project', 'user')
    
    def __str__(self):
        return f"{self.user.username} in {self.project.title} ({self.role})"

class ProjectTask(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='todo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.project.title})"



class ProjectApplication(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_applications')
    message = models.TextField()
    applied_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('project', 'applicant')

    def __str__(self):
        return f"{self.applicant.username}'s application for {self.project.title}"