from django.db.models import F
from accounts.models import CustomUser
from skills.models import SkillExchange, Review

def award_swap_coins(user, amount, reason):
    """
    Award SwapCoins to a user and log the transaction
    """
    user.swap_coins = F('swap_coins') + amount
    user.save(update_fields=['swap_coins'])
    user.refresh_from_db()
    
    # Log the transaction
    Transaction.objects.create(
        user=user,
        amount=amount,
        balance_after=user.swap_coins,
        reason=reason
    )
    return True

def calculate_xp_earned(exchange):
    """
    Calculate XP earned from a skill exchange session
    """
    base_xp = 50
    duration_bonus = min(exchange.duration / 10, 20)  # Max 20 bonus for long sessions
    rating_bonus = 0
    
    try:
        review = Review.objects.get(exchange=exchange)
        rating_bonus = (review.rating - 3) * 10  # Bonus/malus based on rating
    except Review.DoesNotExist:
        pass
    
    total_xp = base_xp + duration_bonus + rating_bonus
    return max(total_xp, 10)  # Minimum 10 XP

def update_user_level(user):
    """
    Update user's level based on their total XP
    """
    xp_needed = {
        1: 0,
        2: 100,
        3: 300,
        4: 600,
        5: 1000,
        6: 1500,
        7: 2100,
        8: 2800,
        9: 3600,
        10: 4500
    }
    
    current_level = user.level
    new_level = current_level
    
    # Find the highest level the user qualifies for
    for level, xp in sorted(xp_needed.items(), reverse=True):
        if user.total_xp >= xp:
            new_level = level
            break
    
    if new_level > current_level:
        user.level = new_level
        user.save(update_fields=['level'])
        
        # Award level-up bonus
        level_bonus = new_level * 50
        award_swap_coins(user, level_bonus, f"Level {new_level} achievement")
        
        # Create notification
        Notification.objects.create(
            user=user,
            message=f"Congratulations! You've reached Level {new_level}",
            is_achievement=True
        )
        
        return True
    return False

def check_achievements(user):
    """
    Check and award achievements based on user activity
    """
    achievements = []
    
    # First session achievement
    if SkillExchange.objects.filter(Q(mentor=user) | Q(learner=user)).count() == 1:
        achievements.append(('first_session', 'Completed First Session'))
    
    # Skill master achievement (taught a skill 5 times)
    from django.db.models import Count
    taught_skills = SkillExchange.objects.filter(mentor=user).values('skill').annotate(
        count=Count('skill')
    ).filter(count__gte=5)
    
    for skill_data in taught_skills:
        skill = SkillCategory.objects.get(id=skill_data['skill'])
        achievements.append((f'skill_master_{skill.id}', f'Skill Master: {skill.name}'))
    
    # Community contributor (created a circle with 10+ members)
    from community.models import SkillCircle, CircleMembership
    popular_circles = SkillCircle.objects.filter(created_by=user).annotate(
        member_count=Count('circlemembership')
    ).filter(member_count__gte=10)
    
    for circle in popular_circles:
        achievements.append((f'community_leader_{circle.id}', f'Community Leader: {circle.name}'))
    
    # Award achievements
    for achievement_id, achievement_name in achievements:
        if not Achievement.objects.filter(user=user, achievement_id=achievement_id).exists():
            Achievement.objects.create(
                user=user,
                achievement_id=achievement_id,
                name=achievement_name
            )
            
            # Award bonus
            award_swap_coins(user, 100, f"Achievement: {achievement_name}")
            
            # Create notification
            Notification.objects.create(
                user=user,
                message=f"Achievement Unlocked: {achievement_name}",
                is_achievement=True
            )
    
    return len(achievements)