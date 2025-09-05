# projects/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from .models import Project, ProjectTeam, ProjectTask
from skills.models import SkillCategory
from accounts.models import CustomUser


@login_required
def project_list(request):
    # Get projects where user is owner or team member
    user_projects = Project.objects.filter(
        Q(owner=request.user) | Q(team_memberships__user=request.user)
    ).distinct().order_by('-created_at')
    
    # Get recommended projects based on user's skills
    user_skills = request.user.userskill_set.filter(
        Q(can_teach=True) | Q(wants_to_learn=True)
    ).values_list('skill', flat=True)
    
    recommended_projects = Project.objects.filter(
        required_skills__in=user_skills,
        is_open=True
    ).exclude(
        Q(owner=request.user) | Q(team_memberships__user=request.user)
    ).distinct().annotate(
        team_count=Count('team_memberships')
    ).order_by('-created_at')[:6]
    
    context = {
        'user_projects': user_projects,
        'recommended_projects': recommended_projects,
    }
    return render(request, 'projects/list.html', context)

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    is_member = ProjectTeam.objects.filter(
        project=project,
        user=request.user
    ).exists()
    is_owner = project.owner == request.user
    
    team_members = project.team_memberships.all().select_related('user')
    tasks = project.project_tasks.all().order_by('-due_date')
    
    if request.method == 'POST':
        if 'join_project' in request.POST and not is_member:
            has_required_skill = request.user.userskill_set.filter(
                skill__in=project.required_skills.all()
            ).exists()
            
            if has_required_skill:
                ProjectTeam.objects.create(
                    project=project,
                    user=request.user,
                    role='contributor'
                )
                messages.success(request, f"You've joined the project '{project.title}'!")
                return redirect('projects:project_detail', project_id=project.id)
            else:
                messages.error(request, "You don't have the required skills for this project")
                return redirect('projects:project_detail', project_id=project.id)
        
        elif 'leave_project' in request.POST and is_member and not is_owner:
            ProjectTeam.objects.filter(
                project=project,
                user=request.user
            ).delete()
            messages.success(request, f"You've left the project '{project.title}'")
            return redirect('projects:project_list')
        
        elif 'add_task' in request.POST and (is_owner or is_member):
            title = request.POST.get('title')
            description = request.POST.get('description')
            assigned_to_id = request.POST.get('assigned_to')
            due_date = request.POST.get('due_date')
            priority = request.POST.get('priority')
            
            assigned_to = None
            if assigned_to_id:
                assigned_to = get_object_or_404(CustomUser, id=assigned_to_id)
                if not ProjectTeam.objects.filter(project=project, user=assigned_to).exists():
                    assigned_to = None
            
            ProjectTask.objects.create(
                project=project,
                title=title,
                description=description,
                assigned_to=assigned_to,
                due_date=due_date,
                priority=priority
            )
            messages.success(request, "Task added successfully!")
            return redirect('projects:project_detail', project_id=project.id)
        
        elif 'edit_project' in request.POST and is_owner:
            project.title = request.POST.get('title')
            project.description = request.POST.get('description')
            project.save()
            
            new_skills = request.POST.getlist('required_skills')
            project.required_skills.clear()
            for skill_id in new_skills:
                skill = get_object_or_404(SkillCategory, id=skill_id)
                project.required_skills.add(skill)
            
            messages.success(request, "Project updated successfully!")
            return redirect('projects:project_detail', project_id=project.id)
        
        elif 'delete_project' in request.POST and is_owner:
            project.delete()
            messages.success(request, "Project deleted successfully!")
            return redirect('projects:project_list')
    
    context = {
        'project': project,
        'is_member': is_member,
        'is_owner': is_owner,
        'team_members': team_members,
        'tasks': tasks,
    }
    return render(request, 'projects/detail.html', context)

@login_required
def create_project(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        required_skills = request.POST.getlist('required_skills')
        
        project = Project.objects.create(
            title=title,
            description=description,
            owner=request.user
        )
        
        for skill_id in required_skills:
            skill = get_object_or_404(SkillCategory, id=skill_id)
            project.required_skills.add(skill)
        
        ProjectTeam.objects.create(
            project=project,
            user=request.user,
            role='lead'
        )
        
        messages.success(request, f"Project '{project.title}' created successfully!")
        return redirect('projects:project_detail', project_id=project.id)
    
    skills = SkillCategory.objects.all()
    context = {
        'skills': skills
    }
    return render(request, 'projects/create.html', context)

@login_required
def manage_task(request, task_id):
    task = get_object_or_404(ProjectTask, id=task_id)
    is_member = ProjectTeam.objects.filter(
        project=task.project,
        user=request.user
    ).exists()
    
    if not is_member:
        messages.error(request, "You don't have permission to manage this task")
        return redirect('projects:project_detail', project_id=task.project.id)
    
    if request.method == 'POST':
        if 'update_status' in request.POST:
            new_status = request.POST.get('status')
            task.status = new_status
            task.save()
            messages.success(request, f"Task status updated to '{task.get_status_display()}'")
            return redirect('projects:project_detail', project_id=task.project.id)
        
        elif 'assign_task' in request.POST:
            assigned_to_id = request.POST.get('assigned_to')
            if assigned_to_id:
                assigned_to = get_object_or_404(CustomUser, id=assigned_to_id)
                if ProjectTeam.objects.filter(project=task.project, user=assigned_to).exists():
                    task.assigned_to = assigned_to
                    task.save()
                    messages.success(request, f"Task assigned to {assigned_to.get_full_name()}")
                    return redirect('projects:project_detail', project_id=task.project.id)
        
        elif 'complete_task' in request.POST:
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save()
            messages.success(request, "Task marked as completed!")
            return redirect('projects:project_detail', project_id=task.project.id)
    
    team_members = task.project.team_memberships.all().select_related('user')
    context = {
        'task': task,
        'team_members': team_members,
    }
    return render(request, 'projects/manage_task.html', context)


@login_required
def add_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    is_member = ProjectTeam.objects.filter(project=project, user=request.user).exists()
    if not is_member:
        messages.error(request, "You must be part of the project to add a task.")
        return redirect('projects:detail', project_id=project_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')
        priority = request.POST.get('priority')

        assigned_to = None
        if assigned_to_id:
            user = get_object_or_404(CustomUser, id=assigned_to_id)
            if ProjectTeam.objects.filter(project=project, user=user).exists():
                assigned_to = user

        ProjectTask.objects.create(
            project=project,
            title=title,
            description=description,
            assigned_to=assigned_to,
            due_date=due_date,
            priority=priority
        )
        messages.success(request, "Task added successfully!")
    return redirect('projects:detail', project_id=project_id)



from django.core.exceptions import ObjectDoesNotExist

@login_required
def invite_member(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if project.owner != request.user:
        messages.error(request, "Only the project owner can invite members.")
        return redirect('projects:detail', project_id=project.id)

    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            if ProjectTeam.objects.filter(project=project, user=user).exists():
                messages.info(request, "User is already a member of this project.")
            else:
                ProjectTeam.objects.create(
                    project=project,
                    user=user,
                    role='contributor'
                )
                messages.success(request, f"{user.get_full_name()} has been added to the project.")
        except ObjectDoesNotExist:
            messages.error(request, "User with that email does not exist.")
        
        return redirect('projects:detail', project_id=project.id)


def join_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project.team_members.add(request.user)
    return redirect('projects:detail', pk=pk)
