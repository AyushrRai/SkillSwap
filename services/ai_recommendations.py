import openai
from django.conf import settings
from django.db.models import Count
from skills.models import SkillCategory, UserSkill
from accounts.models import CustomUser

openai.api_key = settings.OPENAI_API_KEY

def get_skill_recommendations(user):
    """
    Get AI-powered skill recommendations for a user based on their current skills and interests
    """
    # Get user's current skills
    current_skills = list(UserSkill.objects.filter(user=user).values_list('skill__name', flat=True))
    
    # Get popular skills in the platform
    popular_skills = list(SkillCategory.objects.annotate(
        user_count=Count('userskill')
    ).order_by('-user_count')[:10].values_list('name', flat=True))
    
    prompt = f"""
    User's current skills: {', '.join(current_skills)}
    Popular skills on the platform: {', '.join(popular_skills)}
    
    Suggest 5 skills the user might want to learn next based on their current skills and popular trends.
    For each suggestion, provide a brief reason why it would be a good fit.
    Format the response as a bulleted list with skill name and reason.
    
    Suggestions:
    """
    
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error getting AI recommendations: {e}")
        return None

def get_career_path_suggestions(user):
    """
    Get AI-powered career path suggestions based on user's skills
    """
    current_skills = list(UserSkill.objects.filter(user=user).values_list('skill__name', flat=True))
    
    prompt = f"""
    User's current skills: {', '.join(current_skills)}
    
    Suggest 3 potential career paths that align with the user's current skills.
    For each career path, provide:
    - The job title
    - Required skills the user already has
    - Skills they might need to develop
    - Growth potential
    
    Format the response as a clear, organized list with headings for each career path.
    """
    
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error getting career path suggestions: {e}")
        return None

def generate_match_explanation(user1, user2, common_skill):
    """
    Generate an AI-powered explanation of why two users would be a good match
    """
    user1_skills = list(UserSkill.objects.filter(user=user1).values_list('skill__name', flat=True))
    user2_skills = list(UserSkill.objects.filter(user=user2).values_list('skill__name', flat=True))
    
    prompt = f"""
    User 1 ({user1.username}) skills: {', '.join(user1_skills)}
    User 2 ({user2.username}) skills: {', '.join(user2_skills)}
    Common skill for exchange: {common_skill}
    
    Write a brief, friendly explanation (2-3 sentences) of why these two users would be a good match
    for skill exchange, focusing on complementary skills and potential mutual benefits.
    """
    
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error generating match explanation: {e}")
        return None