from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import random

from .models import SkillCategory, UserSkill, SkillExchange, Review
from accounts.models import CustomUser, UserAvailability
from community.models import SkillCircle
from .forms import SkillExchangeForm, ReviewForm
from django.contrib.auth import get_user_model
User = get_user_model()

@login_required
def discover_skills(request):
    categories = SkillCategory.objects.annotate(
        user_count=Count('userskill')
    ).order_by('-user_count')[:12]
    
    # Get user's skills to teach and learn
    teaching_skills = request.user.userskill_set.filter(can_teach=True)
    learning_skills = request.user.userskill_set.filter(wants_to_learn=True)
    
    context = {
        'categories': categories,
        'teaching_skills': teaching_skills,
        'learning_skills': learning_skills,
    }
    return render(request, 'skills/discover.html', context)

@login_required
def skill_categories(request):
    categories = SkillCategory.objects.annotate(
        user_count=Count('userskill')
    ).order_by('name')
    
    return render(request, 'skills/categories.html', {
        'categories': categories
    })

@login_required
def skill_category_detail(request, category_id):
    category = get_object_or_404(SkillCategory, id=category_id)
    
    # Get users who can teach this skill
    mentors = CustomUser.objects.filter(
        userskill__skill=category,
        userskill__can_teach=True
    ).distinct()
    
    # Get users who want to learn this skill
    learners = CustomUser.objects.filter(
        userskill__skill=category,
        userskill__wants_to_learn=True
    ).distinct()
    
    return render(request, 'skills/category_detail.html', {
        'category': category,
        'mentors': mentors,
        'learners': learners
    })

@login_required
def add_skill(request):
    if request.method == 'POST':
        skill_id = request.POST.get('skill_id')
        skill_type = request.POST.get('skill_type')  # 'teaching' or 'learning'
        level = request.POST.get('level', 'beginner')

        if not skill_id:
            messages.error(request, "Please select a valid skill.")
            return redirect('skills:add')

        skill = get_object_or_404(SkillCategory, id=skill_id)

        # Create or update the user skill
        user_skill, created = UserSkill.objects.get_or_create(
            user=request.user,
            skill=skill,
            defaults={
                'level': level,
                'can_teach': skill_type == 'teaching',
                'wants_to_learn': skill_type == 'learning'
            }
        )

        if not created:
            # Update existing skill
            if skill_type == 'teaching':
                user_skill.can_teach = True
            else:
                user_skill.wants_to_learn = True
            user_skill.level = level
            user_skill.save()

        messages.success(request, f"Skill '{skill.name}' added successfully!")
        return redirect('profile')

    # GET request - show form
    categories = SkillCategory.objects.all()
    return render(request, 'skills/add_skill.html', {
        'categories': categories,
        'skill_levels': UserSkill.SKILL_LEVELS
    })
@login_required
def edit_skill(request, skill_id):
    user_skill = get_object_or_404(UserSkill, id=skill_id, user=request.user)
    
    if request.method == 'POST':
        level = request.POST.get('level')
        can_teach = request.POST.get('can_teach') == 'on'
        wants_to_learn = request.POST.get('wants_to_learn') == 'on'
        
        user_skill.level = level
        user_skill.can_teach = can_teach
        user_skill.wants_to_learn = wants_to_learn
        user_skill.save()
        
        messages.success(request, f'Successfully updated {user_skill.skill.name}')
        return redirect('profile')
    
    return render(request, 'skills/edit_skill.html', {
        'user_skill': user_skill,
        'skill_levels': UserSkill.SKILL_LEVELS
    })

@login_required
def remove_skill(request, skill_id):
    user_skill = get_object_or_404(UserSkill, id=skill_id, user=request.user)
    skill_name = user_skill.skill.name
    user_skill.delete()
    
    messages.success(request, f'Successfully removed {skill_name} from your skills')
    return redirect('profile')

@login_required
def find_mentors(request, skill_id):
    skill = get_object_or_404(SkillCategory, id=skill_id)
    user_skill = get_object_or_404(UserSkill, skill=skill, user=request.user, wants_to_learn=True)
    
    # Find users who can teach this skill at or above the level the user wants to learn
    mentors = CustomUser.objects.filter(
        userskill__skill=skill,
        userskill__can_teach=True,
        userskill__level__gte=user_skill.level
    ).exclude(id=request.user.id).distinct()
    
    # Add some match information (simplified)
    for mentor in mentors:
        mentor.match_score = random.randint(60, 95)  # Replace with real matching algorithm
        mentor.availability_overlap = check_availability_overlap(request.user, mentor)
    
    return render(request, 'skills/find_mentors.html', {
        'skill': skill,
        'mentors': sorted(mentors, key=lambda x: x.match_score, reverse=True),
        'user_skill': user_skill
    })

@login_required
def find_learners(request, skill_id):
    skill = get_object_or_404(SkillCategory, id=skill_id)
    user_skill = get_object_or_404(UserSkill, skill=skill, user=request.user, can_teach=True)
    
    # Find users who want to learn this skill at or below the level the user can teach
    learners = CustomUser.objects.filter(
        userskill__skill=skill,
        userskill__wants_to_learn=True,
        userskill__level__lte=user_skill.level
    ).exclude(id=request.user.id).distinct()
    
    # Add some match information (simplified)
    for learner in learners:
        learner.match_score = random.randint(60, 95)  # Replace with real matching algorithm
        learner.availability_overlap = check_availability_overlap(request.user, learner)
    
    return render(request, 'skills/find_learners.html', {
        'skill': skill,
        'learners': sorted(learners, key=lambda x: x.match_score, reverse=True),
        'user_skill': user_skill
    })

@login_required
def initiate_exchange(request, user_id, skill_id):
    partner = get_object_or_404(CustomUser, id=user_id)
    skill = get_object_or_404(SkillCategory, id=skill_id)
    
    if request.user == partner:
        messages.error(request, "You cannot initiate an exchange with yourself")
        return redirect('skills:discover')
    
    # Check if exchange already exists
    existing_exchange = SkillExchange.objects.filter(
        (Q(mentor=request.user) & Q(learner=partner)) |
        (Q(mentor=partner) & Q(learner=request.user)),
        skill=skill,
        status__in=['pending', 'accepted']
    ).first()
    
    if existing_exchange:
        messages.info(request, f"You already have an existing exchange with {partner.username} for {skill.name}")
        return redirect('skills:exchange_detail', exchange_id=existing_exchange.id)
    
    if request.method == 'POST':
        form = SkillExchangeForm(request.user, partner, skill, request.POST)
        if form.is_valid():
            exchange = form.save()
            messages.success(request, f"Skill exchange request sent to {partner.username}")
            return redirect('skills:exchange_detail', exchange_id=exchange.id)
    else:
        form = SkillExchangeForm(request.user, partner, skill)
    
    return render(request, 'skills/initiate_exchange.html', {
        'partner': partner,
        'skill': skill,
        'form': form,
        'suggested_times': suggest_meeting_times(request.user, partner)
    })

@login_required
def exchange_detail(request, exchange_id):
    exchange = get_object_or_404(SkillExchange, id=exchange_id)
    
    if request.user not in [exchange.mentor, exchange.learner]:
        messages.error(request, "You don't have permission to view this exchange")
        return redirect('skills:discover')
    
    # Check if user has already reviewed this exchange
    has_reviewed = Review.objects.filter(
        exchange=exchange,
        reviewer=request.user
    ).exists()
    
    return render(request, 'skills/exchange_detail.html', {
        'exchange': exchange,
        'has_reviewed': has_reviewed,
        'is_mentor': exchange.mentor == request.user
    })

@login_required
def accept_exchange(request, exchange_id):
    exchange = get_object_or_404(SkillExchange, id=exchange_id, learner=request.user, status='pending')
    
    exchange.status = 'accepted'
    exchange.save()
    
    messages.success(request, f"You've accepted the exchange request for {exchange.skill.name}")
    return redirect('skills:exchange_detail', exchange_id=exchange.id)

@login_required
def reject_exchange(request, exchange_id):
    exchange = get_object_or_404(SkillExchange, id=exchange_id, learner=request.user, status='pending')
    
    exchange.status = 'rejected'
    exchange.save()
    
    messages.success(request, f"You've rejected the exchange request for {exchange.skill.name}")
    return redirect('dashboard')

@login_required
def complete_exchange(request, exchange_id):
    exchange = get_object_or_404(SkillExchange, id=exchange_id)
    
    if request.user not in [exchange.mentor, exchange.learner]:
        messages.error(request, "You don't have permission to complete this exchange")
        return redirect('skills:discover')
    
    exchange.status = 'completed'
    exchange.save()
    
    messages.success(request, f"Marked exchange for {exchange.skill.name} as completed")
    return redirect('skills:exchange_detail', exchange_id=exchange.id)

@login_required
def submit_review(request, exchange_id):
    exchange = get_object_or_404(SkillExchange, id=exchange_id)
    
    if request.user not in [exchange.mentor, exchange.learner]:
        messages.error(request, "You don't have permission to review this exchange")
        return redirect('skills:discover')
    
    # Determine who is being reviewed
    reviewed_user = exchange.learner if exchange.mentor == request.user else exchange.mentor
    
    if Review.objects.filter(exchange=exchange, reviewer=request.user).exists():
        messages.warning(request, "You've already reviewed this exchange")
        return redirect('skills:exchange_detail', exchange_id=exchange.id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.exchange = exchange
            review.reviewer = request.user
            review.reviewed_user = reviewed_user
            review.save()
            
            messages.success(request, "Thank you for your review!")
            return redirect('skills:exchange_detail', exchange_id=exchange.id)
    else:
        form = ReviewForm()
    
    return render(request, 'skills/submit_review.html', {
        'exchange': exchange,
        'reviewed_user': reviewed_user,
        'form': form
    })

@login_required
def schedule_exchange(request, skill_id=None):
    # Handle case when skill_id is not provided (from schedule/ URL)
    if skill_id is None:
        # Get user's upcoming exchanges
        upcoming = SkillExchange.objects.filter(
            Q(mentor=request.user) | Q(learner=request.user),
            status='accepted',
            scheduled_time__gte=timezone.now()
        ).order_by('scheduled_time')
        
        return render(request, 'skills/schedule.html', {
            'upcoming_exchanges': upcoming
        })
    
    # Handle case when skill_id is provided (from schedule/<skill_id>/ URL)
    skill = get_object_or_404(SkillCategory, pk=skill_id)
    
    if request.method == 'POST':
        form = SkillExchangeForm(request.POST)
        if form.is_valid():
            exchange = form.save(commit=False)
            exchange.skill = skill
            exchange.requester = request.user
            exchange.status = 'pending'
            exchange.save()
            
            messages.success(request, 'Exchange scheduled successfully!')
            return redirect('skills:my_exchanges')
    
    else:
        form = SkillExchangeForm()
    
    return render(request, 'skills/schedule_exchange.html', {
        'skill': skill,
        'form': form
    })

@login_required
def my_exchanges(request):
    # Get all user's exchanges
    exchanges = SkillExchange.objects.filter(
        Q(mentor=request.user) | Q(learner=request.user)
    ).order_by('-created_at')
    
    return render(request, 'skills/my_exchanges.html', {
        'exchanges': exchanges
    })

# Helper functions
def check_availability_overlap(user1, user2):
    """Check if two users have overlapping availability"""
    # Simplified version - in reality would compare their availability slots
    return random.choice(["High", "Medium", "Low"])

def suggest_meeting_times(user1, user2):
    """Suggest meeting times based on both users' availability"""
    # This is a simplified version - real implementation would analyze calendars
    base_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    suggested_times = []
    for i in range(1, 8):  # Next 7 days
        day = base_date + timedelta(days=i)
        for hour in [10, 14, 18]:  # Suggest at 10am, 2pm, 6pm
            suggested_times.append(day.replace(hour=hour))
    
    return suggested_times[:5]  # Return top 5 suggestions



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SkillExchange

@login_required
def schedule_exchange(request, skill_id):
    skill = get_object_or_404(Skill, pk=skill_id)
    
    if request.method == 'POST':
        # Process form data
        exchange_date = request.POST.get('exchange_date')
        exchange_time = request.POST.get('exchange_time')
        duration = request.POST.get('duration')
        meeting_type = request.POST.get('meeting_type')
        location = request.POST.get('location', '')
        notes = request.POST.get('notes', '')
        
        # Create new exchange
        exchange = SkillExchange.objects.create(
            skill=skill,
            requester=request.user,
            exchange_date=exchange_date,
            exchange_time=exchange_time,
            duration=duration,
            meeting_type=meeting_type,
            location=location,
            notes=notes,
            status='pending'
        )
        
        messages.success(request, 'Exchange scheduled successfully!')
        return redirect('skills:my_exchanges')
    
    return render(request, 'skills/schedule.html', {
        'skill_id': skill_id,
        'skill': skill
    })




# Add to skills/views.py
from django.db.models import Q

@login_required
def discover_users(request):
    # Get all users except the current user
    all_users = CustomUser.objects.all().exclude(id=request.user.id)
    
    # Get search query if exists
    search_query = request.GET.get('search', '')
    
    if search_query:
        all_users = all_users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    return render(request, 'skills/discover_users.html', {
        'users': all_users,
        'search_query': search_query
    })




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import SkillRequest, CommunicationSession
from .forms import SkillRequestForm
import uuid

@login_required
def send_skill_request(request, username):
    receiver = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        form = SkillRequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.requester = request.user
            request_obj.receiver = receiver
            request_obj.save()
            messages.success(request, 'Your request has been sent successfully!')
            return redirect('public_profile', username=username)
    else:
        form = SkillRequestForm()
    
    return render(request, 'skills/send_request.html', {
        'form': form,
        'receiver': receiver
    })

@login_required
def view_requests(request):
    # Received requests (where the user is the receiver)
    received_requests = SkillRequest.objects.filter(
        receiver=request.user
    ).select_related('requester', 'skill').order_by('-created_at')

    # Sent requests (where the user is the requester/sender)
    sent_requests = SkillRequest.objects.filter(
        requester=request.user
    ).select_related('receiver', 'skill').order_by('-created_at')

    # Optional: If you want to show all requests (sent + received together)
    all_requests = SkillRequest.objects.filter(
        Q(receiver=request.user) | Q(requester=request.user)
    ).select_related('requester', 'receiver', 'skill').order_by('-created_at')

    context = {
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'all_requests': all_requests,  # only needed if your template uses it
    }

    return render(request, 'skills/view_requests.html', context)

@login_required
def handle_request(request, request_id, action):
    skill_request = get_object_or_404(
        SkillRequest,
        id=request_id,
        receiver=request.user
    )
    
    if action == 'accept':
        skill_request.status = 'accepted'
        messages.success(request, 'Request accepted!')
    elif action == 'reject':
        skill_request.status = 'rejected'
        messages.info(request, 'Request rejected.')
    
    skill_request.save()
    return redirect('skills:view_requests')
@login_required
def manage_request(request, request_id, action):
    skill_request = get_object_or_404(SkillRequest, id=request_id, receiver=request.user)
    
    if action == 'accept':
        skill_request.status = 'accepted'
        # Create a communication session
        room_id = str(uuid.uuid4())
        CommunicationSession.objects.create(
            request=skill_request,
            room_id=room_id,
            is_active=True
        )
        messages.success(request, 'Request accepted! Communication session created.')
    elif action == 'reject':
        skill_request.status = 'rejected'
        messages.info(request, 'Request rejected.')
    
    skill_request.save()
    return redirect('my_requests')

@login_required
def my_requests(request):
    received_requests = SkillRequest.objects.filter(receiver=request.user).order_by('-created_at')
    sent_requests = SkillRequest.objects.filter(requester=request.user).order_by('-created_at')
    
    return render(request, 'skills/my_requests.html', {
        'received_requests': received_requests,
        'sent_requests': sent_requests
    })

@login_required
def communication_room(request, request_id):
    skill_request = get_object_or_404(SkillRequest, id=request_id)
    
    # Verify user is part of this request
    if request.user not in [skill_request.requester, skill_request.receiver]:
        messages.error(request, 'You are not authorized to access this communication.')
        return redirect('dashboard')
    
    # Ensure request is accepted
    if skill_request.status != 'accepted':
        messages.error(request, 'This request needs to be accepted first.')
        return redirect('skills:view_requests')
    
    # Get or create communication session if it doesn't exist
    session, created = CommunicationSession.objects.get_or_create(
        request=skill_request,
        defaults={'room_id': str(uuid.uuid4())}
    )
    
    other_user = skill_request.requester if request.user == skill_request.receiver else skill_request.receiver
    
    return render(request, 'skills/communication_room.html', {
        'session': session,
        'other_user': other_user,
        'skill_request': skill_request
    })
@login_required
def accept_request(request, request_id):
    skill_request = get_object_or_404(SkillRequest, id=request_id, receiver=request.user)
    
    if skill_request.status != 'pending':
        messages.warning(request, 'This request has already been processed.')
        return redirect('skills:view_requests')
    
    skill_request.status = 'accepted'
    skill_request.save()
    
    # Get or create communication session
    session, created = CommunicationSession.objects.get_or_create(
        request=skill_request,
        defaults={'room_id': str(uuid.uuid4())}
    )
    
    messages.success(request, 'Request accepted! Video call option is now available.')
    return redirect('skills:communication_room', request_id=skill_request.id)


def reject_request(request, request_id):
    skill_request = get_object_or_404(SkillRequest, id=request_id)
    # Add any permission checks here (e.g., only the receiver can reject)
    if request.user == skill_request.receiver:
        skill_request.status = 'rejected'
        skill_request.save()
        # Optional: Add a message to show the request was rejected
        messages.success(request, "Request has been rejected.")
    return redirect('skills:view_requests')




