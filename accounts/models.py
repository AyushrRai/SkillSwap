from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    bio = models.TextField(_('About you'), blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    is_verified = models.BooleanField(default=False)
    swap_coins = models.PositiveIntegerField(default=100)  # Starting balance
    
    def __str__(self):
        return self.username

    def get_profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return '/static/accounts/images/default_profile.jpg'

class UserAvailability(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    day = models.CharField(max_length=10, choices=[
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        verbose_name_plural = 'User availabilities'
        ordering = ['day', 'start_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.day} {self.start_time}-{self.end_time}"


from django.contrib.auth import get_user_model

class Availability(models.Model):
    DAY_CHOICES = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        verbose_name_plural = "Availabilities"
        ordering = ['day', 'start_time']
    
    def __str__(self):
        return f"{self.get_day_display()} {self.start_time}-{self.end_time}"