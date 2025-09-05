from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import MiniCourse, CourseModule, ModuleContent, CourseEnrollment
from skills.models import SkillCategory

@login_required
def course_list(request):
    # Get courses based on user's skills
    user_skills = request.user.userskill_set.filter(
        Q(can_teach=True) | Q(wants_to_learn=True)
    ).values_list('skill', flat=True)
    
    recommended_courses = MiniCourse.objects.filter(
        skill__in=user_skills
    ).annotate(
        enrollment_count=Count('courseenrollment')
    ).order_by('-enrollment_count')[:6]
    
    popular_courses = MiniCourse.objects.annotate(
        enrollment_count=Count('courseenrollment')
    ).order_by('-enrollment_count')[:6]
    
    new_courses = MiniCourse.objects.order_by('-created_at')[:6]
    
    context = {
        'recommended_courses': recommended_courses,
        'popular_courses': popular_courses,
        'new_courses': new_courses,
    }
    return render(request, 'courses/list.html', context)

@login_required
def courses_by_category(request, category_id):
    category = get_object_or_404(SkillCategory, id=category_id)
    courses = MiniCourse.objects.filter(skill=category).annotate(
        enrollment_count=Count('courseenrollment')
    ).order_by('-enrollment_count')
    
    context = {
        'category': category,
        'courses': courses,
    }
    return render(request, 'courses/courses_by_category.html', context)

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(MiniCourse, id=course_id)
    is_enrolled = CourseEnrollment.objects.filter(
        course=course,
        user=request.user
    ).exists()
    
    modules = course.modules.all().prefetch_related('contents')
    
    if request.method == 'POST' and 'enroll' in request.POST:
        if not is_enrolled:
            if course.is_free or request.user.swap_coins >= course.price:
                if not course.is_free:
                    request.user.swap_coins -= course.price
                    request.user.save()
                
                CourseEnrollment.objects.create(
                    course=course,
                    user=request.user
                )
                messages.success(request, f"You've enrolled in '{course.title}'!")
                return redirect('courses:course_detail', course_id=course.id)
            else:
                messages.error(request, "You don't have enough SwapCoins to enroll in this course")
                return redirect('courses:course_detail', course_id=course.id)
    
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'modules': modules,
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
def create_course(request):
    if not request.user.userskill_set.filter(can_teach=True).exists():
        messages.error(request, "You need to have teaching skills to create a course")
        return redirect('courses:course_list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        skill_id = request.POST.get('skill')
        level = request.POST.get('level')
        is_free = request.POST.get('is_free') == 'on'
        price = request.POST.get('price', 0)
        
        skill = get_object_or_404(SkillCategory, id=skill_id)
        
        course = MiniCourse.objects.create(
            title=title,
            description=description,
            skill=skill,
            creator=request.user,
            level=level,
            is_free=is_free,
            price=price if not is_free else 0
        )
        
        messages.success(request, f"Course '{course.title}' created successfully! Now add modules and content.")
        return redirect('courses:manage_course', course_id=course.id)
    
    teaching_skills = request.user.userskill_set.filter(can_teach=True)
    context = {
        'teaching_skills': teaching_skills
    }
    return render(request, 'courses/create_course.html', context)

@login_required
def manage_course(request, course_id):
    course = get_object_or_404(MiniCourse, id=course_id, creator=request.user)
    
    if request.method == 'POST':
        if 'add_module' in request.POST:
            module_title = request.POST.get('module_title')
            module_description = request.POST.get('module_description', '')
            
            module = CourseModule.objects.create(
                course=course,
                title=module_title,
                description=module_description
            )
            messages.success(request, f"Module '{module.title}' added successfully!")
            return redirect('courses:manage_course', course_id=course.id)
        
        elif 'add_content' in request.POST:
            module_id = request.POST.get('module_id')
            content_type = request.POST.get('content_type')
            title = request.POST.get('title')
            content = request.POST.get('content')
            is_free_preview = request.POST.get('is_free_preview') == 'on'
            
            module = get_object_or_404(CourseModule, id=module_id, course=course)
            
            ModuleContent.objects.create(
                module=module,
                title=title,
                content_type=content_type,
                content=content,
                is_free_preview=is_free_preview
            )
            messages.success(request, "Content added successfully!")
            return redirect('courses:manage_course', course_id=course.id)
    
    modules = course.modules.all().prefetch_related('contents')
    context = {
        'course': course,
        'modules': modules,
    }
    return render(request, 'courses/manage_course.html', context)