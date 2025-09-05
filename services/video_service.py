import secrets
import string
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

def generate_meeting_link(user1, user2, skill_name):
    """
    Generate a unique Jitsi meeting link for a skill exchange session
    """
    # Create a unique meeting ID
    chars = string.ascii_lowercase + string.digits
    meeting_id = f"skillswap-{user1.id}-{user2.id}-{skill_name.lower().replace(' ', '-')}-{''.join(secrets.choice(chars) for _ in range(8))}"
    
    # Generate the Jitsi meeting URL
    meeting_url = f"https://meet.jit.si/{meeting_id}"
    
    return meeting_url

def generate_meeting_credentials():
    """
    Generate credentials for meeting moderation (if needed)
    """
    return {
        'moderator_password': secrets.token_urlsafe(12),
        'attendee_password': secrets.token_urlsafe(8)
    }

def schedule_recurring_meetings(start_time, recurrence_count, interval_days):
    """
    Generate a series of meeting times for recurring sessions
    """
    meetings = []
    for i in range(recurrence_count):
        meeting_time = start_time + timedelta(days=i * interval_days)
        meetings.append(meeting_time)
    return meetings

def add_to_google_calendar(user, meeting_details):
    """
    Add a meeting to user's Google Calendar (simplified - would use Google API in reality)
    """
    # In a real implementation, this would use the Google Calendar API
    # with the user's OAuth credentials
    return True

def send_meeting_reminder(user, meeting):
    """
    Send a meeting reminder to the user (simplified)
    """
    # In a real implementation, this would send an email or notification
    subject = f"Reminder: {meeting.skill.name} session with {meeting.get_partner(user).username}"
    message = f"""
    Your skill exchange session is coming up!
    
    Details:
    - Skill: {meeting.skill.name}
    - Partner: {meeting.get_partner(user).get_full_name()}
    - Time: {meeting.scheduled_time.strftime('%A, %B %d at %H:%M')}
    - Duration: {meeting.duration} minutes
    - Meeting Link: {meeting.meeting_link}
    
    See you there!
    """
    
    # In reality, would use Django's email sending functionality
    print(f"Would send email to {user.email} with subject: {subject}")
    return True