# views.py
from django.db.models import Exists
from django.db.models import OuterRef
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST

from .models import (
    SkillCircle, CircleMembership, CirclePost, 
    CircleEvent, PostLike, PostComment,
    CircleResource, CircleInvitation, CircleNotification
)
from skills.models import SkillCategory
from .forms import (
    SkillCircleForm, CirclePostForm, EventForm,
    ResourceForm, InvitationForm, CommentForm,
    MembershipRequestForm, CircleSearchForm
)

@login_required
def circle_list(request):
    form = CircleSearchForm(request.GET or None)
    
    # Base queryset with member count
    circles = SkillCircle.objects.filter(is_active=True).annotate(
        member_count=Count('circlemembership')
    ).order_by('-created_at')
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        skill = form.cleaned_data.get('skill')
        privacy = form.cleaned_data.get('privacy')
        
        if query:
            circles = circles.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            )
        if skill:
            circles = circles.filter(skill=skill)
        if privacy:
            circles = circles.filter(privacy=privacy)
    
    # Get popular categories for circles
    popular_categories = SkillCategory.objects.annotate(
        circle_count=Count('skillcircle')
    ).order_by('-circle_count')[:8]
    
    # Get circles user is member of with favorite status
    user_circles = SkillCircle.objects.filter(
        circlemembership__user=request.user,
        circlemembership__status='approved'
    ).annotate(
        member_count=Count('circlemembership'),
        is_favorite=Exists(
            CircleMembership.objects.filter(
                circle=OuterRef('pk'),
                user=request.user,
                is_favorite=True
            )
        )
    ).order_by('-circlemembership__joined_at').distinct()
    
    # Get recommended circles based on user's skills
    recommended_circles = circles.filter(
        skill__userskill__user=request.user
    ).exclude(
        circlemembership__user=request.user
    ).order_by('-member_count')[:6]
    
    # Pagination with favorite status for circles where user is member
    paginator = Paginator(circles, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Annotate favorite status for the paginated results
    circle_ids = [circle.id for circle in page_obj]
    favorites = set(CircleMembership.objects.filter(
        circle_id__in=circle_ids,
        user=request.user,
        is_favorite=True
    ).values_list('circle_id', flat=True))
    
    for circle in page_obj:
        circle.is_favorite = circle.id in favorites
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'popular_categories': popular_categories,
        'user_circles': user_circles,
        'recommended_circles': recommended_circles,
    }
    return render(request, 'community/circle_list.html', context)

@login_required
def circle_detail(request, circle_id):
    circle = get_object_or_404(SkillCircle, id=circle_id, is_active=True)
    membership = CircleMembership.objects.filter(
        circle=circle,
        user=request.user
    ).first()
    
    is_member = membership is not None and membership.status == 'approved'
    is_admin = is_member and membership.role in ['admin', 'moderator']
    
    # Handle membership requests for private circles
    if circle.privacy == 'private' and not is_member:
        if request.method == 'POST' and 'request_join' in request.POST:
            form = MembershipRequestForm(request.POST)
            if form.is_valid():
                CircleMembership.objects.create(
                    circle=circle,
                    user=request.user,
                    role='member',
                    status='pending',
                )
                # Notify admins
                notify_admins(
                    circle=circle,
                    notification_type='membership_request',
                    message=f"{request.user.get_full_name()} requested to join {circle.name}",
                    sender=request.user
                )
                messages.success(request, "Your request has been submitted for approval.")
                return redirect('community:circle_detail', circle_id=circle.id)
        else:
            form = MembershipRequestForm()
        
        context = {
            'circle': circle,
            'is_member': False,
            'is_admin': False,
            'form': form,
            'request_pending': CircleMembership.objects.filter(
                circle=circle,
                user=request.user,
                status='pending'
            ).exists()
        }
        return render(request, 'community/private_circle_request.html', context)
    
    # Handle regular circle access
    posts = CirclePost.objects.filter(circle=circle).order_by('-is_pinned', '-created_at')[:10]
    upcoming_events = CircleEvent.objects.filter(
        circle=circle,
        start_time__gte=timezone.now()
    ).order_by('start_time')[:3]
    members = CircleMembership.objects.filter(
        circle=circle,
        status='approved'
    ).select_related('user').order_by('-role', '-joined_at')[:12]
    resources = CircleResource.objects.filter(
        circle=circle,
        is_approved=True
    ).order_by('-uploaded_at')[:5]
    
    # Post form
    post_form = CirclePostForm(request.POST or None)
    
    if request.method == 'POST':
        if 'join_circle' in request.POST and not is_member:
            if circle.is_full():
                messages.error(request, "This circle has reached its member limit.")
            else:
                CircleMembership.objects.create(
                    circle=circle,
                    user=request.user,
                    role='member'
                )
                messages.success(request, f"You've joined the {circle.name} circle!")
            return redirect('community:circle_detail', circle_id=circle.id)
        
        if 'leave_circle' in request.POST and is_member:
            membership.delete()
            messages.success(request, f"You've left the {circle.name} circle.")
            return redirect('community:circle_detail', circle_id=circle.id)
        
        if 'create_post' in request.POST and is_member and post_form.is_valid():
            post = post_form.save(commit=False)
            post.circle = circle
            post.author = request.user
            post.save()
            messages.success(request, "Your post has been published!")
            return redirect('community:circle_detail', circle_id=circle.id)
    
    context = {
        'circle': circle,
        'is_member': is_member,
        'is_admin': is_admin,
        'membership': membership,
        'posts': posts,
        'upcoming_events': upcoming_events,
        'members': members,
        'resources': resources,
        'post_form': post_form,
    }
    return render(request, 'community/circle_detail.html', context)

@login_required
def create_circle(request):
    if request.method == 'POST':
        form = SkillCircleForm(request.POST, request.FILES)
        if form.is_valid():
            circle = form.save(commit=False)
            circle.created_by = request.user
            circle.save()
            
            # Add creator as admin
            CircleMembership.objects.create(
                circle=circle,
                user=request.user,
                role='admin'
            )
            
            messages.success(request, "Your circle has been created!")
            return redirect('community:circle_detail', circle_id=circle.id)
    else:
        form = SkillCircleForm()
    
    return render(request, 'community/create_circle.html', {'form': form})

@login_required
def edit_circle(request, circle_id):
    circle = get_object_or_404(SkillCircle, id=circle_id, is_active=True)
    membership = CircleMembership.objects.filter(
        circle=circle,
        user=request.user,
        role__in=['admin', 'moderator']
    ).first()
    
    if not membership:
        return HttpResponseForbidden("You don't have permission to edit this circle")
    
    if request.method == 'POST':
        form = SkillCircleForm(request.POST, request.FILES, instance=circle)
        if form.is_valid():
            form.save()
            messages.success(request, "Circle updated successfully!")
            return redirect('community:circle_detail', circle_id=circle.id)
    else:
        form = SkillCircleForm(instance=circle)
    
    return render(request, 'community/edit_circle.html', {'form': form, 'circle': circle})

@login_required
def create_event(request, circle_id):
    circle = get_object_or_404(SkillCircle, id=circle_id, is_active=True)
    membership = CircleMembership.objects.filter(
        circle=circle,
        user=request.user,
        status='approved'
    ).first()
    
    if not membership:
        messages.error(request, "You must be a member to create events")
        return redirect('community:circle_detail', circle_id=circle.id)
    
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.circle = circle
            event.created_by = request.user
            event.save()
            
            # Notify members
            notify_members(
                circle=circle,
                notification_type='new_event',
                message=f"New event created: {event.title}",
                related_event=event
            )
            
            messages.success(request, f"Event '{event.title}' created successfully!")
            return redirect('community:event_detail', event_id=event.id)
    else:
        # Suggest default times (next Saturday 2-4pm)
        next_saturday = timezone.now() + timedelta(days=(5 - timezone.now().weekday() + 7) % 7)
        default_start = next_saturday.replace(hour=14, minute=0, second=0, microsecond=0)
        default_end = default_start + timedelta(hours=2)
        
        form = EventForm(initial={
            'start_time': default_start,
            'end_time': default_end,
        })
    
    context = {
        'circle': circle,
        'form': form,
    }
    return render(request, 'community/create_event.html', context)

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(CircleEvent, id=event_id, circle__is_active=True)
    circle = event.circle
    membership = CircleMembership.objects.filter(
        circle=circle,
        user=request.user,
        status='approved'
    ).first()
    
    is_member = membership is not None
    is_registered = is_member and EventRegistration.objects.filter(
        event=event,
        user=request.user
    ).exists()
    can_register = is_member and not is_registered and event.is_upcoming()
    
    if request.method == 'POST':
        if 'register' in request.POST and can_register:
            if event.max_participants > 0 and event.participant_count() >= event.max_participants:
                messages.error(request, "This event has reached its maximum capacity.")
            else:
                EventRegistration.objects.create(
                    event=event,
                    user=request.user
                )
                messages.success(request, "You've successfully registered for this event!")
            return redirect('community:event_detail', event_id=event.id)
        
        if 'unregister' in request.POST and is_registered:
            registration = EventRegistration.objects.get(
                event=event,
                user=request.user
            )
            registration.delete()
            messages.success(request, "You've unregistered from this event.")
            return redirect('community:event_detail', event_id=event.id)
    
    registrations = EventRegistration.objects.filter(event=event).select_related('user')
    
    context = {
        'event': event,
        'circle': circle,
        'is_member': is_member,
        'is_registered': is_registered,
        'can_register': can_register,
        'registrations': registrations,
    }
    return render(request, 'community/event_detail.html', context)

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(CirclePost, id=post_id, circle__is_active=True)
    circle = post.circle
    membership = CircleMembership.objects.filter(
        circle=circle,
        user=request.user,
        status='approved'
    ).first()
    
    is_member = membership is not None
    is_author = post.author == request.user
    is_admin = is_member and membership.role in ['admin', 'moderator']
    
    comments = PostComment.objects.filter(post=post, parent_comment__isnull=True)
    comment_form = CommentForm(request.POST or None)
    
    if request.method == 'POST':
        if 'add_comment' in request.POST and is_member and comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            
            # Notify post author if it's not them
            if post.author != request.user:
                CircleNotification.objects.create(
                    user=post.author,
                    circle=circle,
                    notification_type='new_comment',
                    message=f"{request.user.get_full_name()} commented on your post",
                    related_post=post
                )
            
            messages.success(request, "Your comment has been added!")
            return redirect('community:post_detail', post_id=post.id)
        
        if 'delete_post' in request.POST and (is_author or is_admin):
            post.delete()
            messages.success(request, "Post deleted successfully")
            return redirect('community:circle_detail', circle_id=circle.id)
        
        if 'pin_post' in request.POST and is_admin:
            post.is_pinned = not post.is_pinned
            post.save()
            action = "pinned" if post.is_pinned else "unpinned"
            messages.success(request, f"Post has been {action}")
            return redirect('community:post_detail', post_id=post.id)
    
    context = {
        'post': post,
        'circle': circle,
        'is_member': is_member,
        'is_author': is_author,
        'is_admin': is_admin,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'community/post_detail.html', context)

@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(CirclePost, id=post_id, circle__is_active=True)
    membership = CircleMembership.objects.filter(
        circle=post.circle,
        user=request.user,
        status='approved'
    ).first()
    
    if not membership:
        return JsonResponse({'error': 'Not a member'}, status=403)
    
    like, created = PostLike.objects.get_or_create(
        post=post,
        user=request.user
    )
    
    if not created:
        like.delete()
    
    return JsonResponse({
        'liked': created,
        'like_count': post.like_count()
    })

@login_required
def circle_members(request, circle_id):
    circle = get_object_or_404(SkillCircle, id=circle_id, is_active=True)
    membership = CircleMembership.objects.filter(
        circle=circle,
        user=request.user,
        status='approved'
    ).first()
    
    if not membership:
        messages.error(request, "You must be a member to view this page")
        return redirect('community:circle_detail', circle_id=circle.id)
    
    members = CircleMembership.objects.filter(
        circle=circle,
        status='approved'
    ).select_related('user').order_by('-role', '-joined_at')
    
    # Handle membership management for admins
    if request.method == 'POST' and membership.role in ['admin', 'moderator']:
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        if user_id and action:
            target_member = get_object_or_404(CircleMembership, circle=circle, user__id=user_id)
            
            if action == 'promote' and membership.role == 'admin':
                if target_member.role == 'member':
                    target_member.role = 'moderator'
                    target_member.save()
                    messages.success(request, f"{target_member.user.get_full_name()} promoted to moderator")
            
            elif action == 'demote' and membership.role == 'admin':
                if target_member.role == 'moderator':
                    target_member.role = 'member'
                    target_member.save()
                    messages.success(request, f"{target_member.user.get_full_name()} demoted to member")
            
            elif action == 'remove':
                if (target_member.role != 'admin' or 
                    (target_member.role == 'admin' and membership.role == 'admin')):
                    target_member.delete()
                    messages.success(request, f"{target_member.user.get_full_name()} removed from circle")
            
            elif action == 'ban':
                target_member.status = 'banned'
                target_member.save()
                messages.success(request, f"{target_member.user.get_full_name()} banned from circle")
            
            return redirect('community:circle_members', circle_id=circle.id)
    
    context = {
        'circle': circle,
        'members': members,
        'is_admin': membership.role in ['admin', 'moderator'],
        'user_role': membership.role,
    }
    return render(request, 'community/circle_members.html', context)

@login_required
def circle_resources(request, circle_id):
    circle = get_object_or_404(SkillCircle, id=circle_id, is_active=True)
    membership = CircleMembership.objects.filter(
        circle=circle,
        user=request.user,
        status='approved'
    ).first()
    
    if not membership:
        messages.error(request, "You must be a member to view this page")
        return redirect('community:circle_detail', circle_id=circle.id)
    
    resources = CircleResource.objects.filter(circle=circle)
    form = ResourceForm(request.POST or None, request.FILES or None)
    
    if request.method == 'POST' and form.is_valid():
        resource = form.save(commit=False)
        resource.circle = circle
        resource.uploaded_by = request.user
        resource.is_approved = membership.role in ['admin', 'moderator']
        resource.save()
        
        messages.success(request, "Resource uploaded successfully!")
        return redirect('community:circle_resources', circle_id=circle.id)
    
    context = {
        'circle': circle,
        'resources': resources,
        'form': form,
        'can_upload': True,
        'can_approve': membership.role in ['admin', 'moderator'],
    }
    return render(request, 'community/circle_resources.html', context)

@login_required
def manage_requests(request, circle_id):
    circle = get_object_or_404(SkillCircle, id=circle_id, is_active=True)
    membership = CircleMembership.objects.filter(
        circle=circle,
        user=request.user,
        role__in=['admin', 'moderator']
    ).first()
    
    if not membership:
        messages.error(request, "You don't have permission to view this page")
        return redirect('community:circle_detail', circle_id=circle.id)
    
    pending_requests = CircleMembership.objects.filter(
        circle=circle,
        status='pending'
    ).select_related('user')
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        
        if request_id and action:
            membership_request = get_object_or_404(CircleMembership, id=request_id)
            
            if action == 'approve':
                membership_request.status = 'approved'
                membership_request.save()
                
                # Notify user
                CircleNotification.objects.create(
                    user=membership_request.user,
                    circle=circle,
                    notification_type='membership_approved',
                    message=f"Your request to join {circle.name} has been approved"
                )
                
                messages.success(request, f"Request from {membership_request.user.get_full_name()} approved")
            
            elif action == 'reject':
                membership_request.delete()
                messages.success(request, f"Request from {membership_request.user.get_full_name()} rejected")
            
            return redirect('community:manage_requests', circle_id=circle.id)
    
    context = {
        'circle': circle,
        'pending_requests': pending_requests,
    }
    return render(request, 'community/manage_requests.html', context)

@login_required
def invite_member(request, circle_id):
    circle = get_object_or_404(SkillCircle, id=circle_id, is_active=True)
    membership = CircleMembership.objects.filter(
        circle=circle,
        user=request.user,
        role__in=['admin', 'moderator']
    ).first()
    
    if not membership:
        messages.error(request, "You don't have permission to invite members")
        return redirect('community:circle_detail', circle_id=circle.id)
    
    form = InvitationForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        
        # Check if user already exists
        try:
            user = User.objects.get(email=email)
            # Check if already a member
            if CircleMembership.objects.filter(circle=circle, user=user).exists():
                messages.warning(request, "This user is already a member of the circle")
                return redirect('community:invite_member', circle_id=circle.id)
            
            # Add directly if circle is public
            if circle.privacy == 'public':
                CircleMembership.objects.create(
                    circle=circle,
                    user=user,
                    role='member'
                )
                messages.success(request, f"{user.get_full_name()} has been added to the circle")
            else:
                # For private circles, create pending membership
                CircleMembership.objects.create(
                    circle=circle,
                    user=user,
                    role='member',
                    status='pending'
                )
                messages.success(request, f"Invitation sent to {user.get_full_name()}")
            
            return redirect('community:circle_members', circle_id=circle.id)
        
        except User.DoesNotExist:
            # Create invitation for non-existing user
            token = generate_token()
            CircleInvitation.objects.create(
                circle=circle,
                email=email,
                invited_by=request.user,
                token=token
            )
            
            # Send email invitation (in real app, you'd implement this)
            # send_invitation_email(email, circle, token)
            
            messages.success(request, f"Invitation sent to {email}")
            return redirect('community:circle_members', circle_id=circle.id)
    
    context = {
        'circle': circle,
        'form': form,
    }
    return render(request, 'community/invite_member.html', context)

@login_required
def notifications(request):
    notifications = CircleNotification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]
    
    # Mark as read
    unread_notifications = notifications.filter(is_read=False)
    if unread_notifications.exists():
        unread_notifications.update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'community/notifications.html', context)

# Helper functions
def notify_admins(circle, notification_type, message, sender=None, related_post=None, related_event=None):
    admins = CircleMembership.objects.filter(
        circle=circle,
        role__in=['admin', 'moderator']
    ).exclude(user=sender).select_related('user')
    
    for admin in admins:
        CircleNotification.objects.create(
            user=admin.user,
            circle=circle,
            notification_type=notification_type,
            message=message,
            related_post=related_post,
            related_event=related_event
        )

def notify_members(circle, notification_type, message, related_post=None, related_event=None):
    members = CircleMembership.objects.filter(
        circle=circle,
        status='approved'
    ).exclude(user=related_post.author if related_post else None).select_related('user')
    
    for member in members:
        CircleNotification.objects.create(
            user=member.user,
            circle=circle,
            notification_type=notification_type,
            message=message,
            related_post=related_post,
            related_event=related_event
        )

def generate_token():
    import secrets
    return secrets.token_urlsafe(32)



from django.shortcuts import redirect, get_object_or_404

def leave_circle(request, circle_id):
    circle = get_object_or_404(Circle, id=circle_id)
    circle.members.remove(request.user)
    return redirect('community:circle_list')



from django.shortcuts import render, redirect, get_object_or_404
from .models import Circle

def create_post(request, circle_id):
    circle = get_object_or_404(Circle, id=circle_id)
    
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.circle = circle
            post.author = request.user
            post.save()
            return redirect('community:circle_detail', circle_id=circle.id)
    else:
        form = PostForm()

    return render(request, 'community/create_post.html', {'form': form, 'circle': circle})

