from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import CreateView

from .forms import CustomUserCreationForm, ProfileEditForm, AvailabilityForm
from .models import CustomUser, UserAvailability
from skills.models import UserSkill, SkillCategory
from skills.models import SkillExchange
from django.db.models import Q

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)
            self.request.session.modified = True
        return super().form_valid(form)

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        messages.success(self.request, 'Account created successfully!')
        return response

class CustomPasswordChangeView(PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('password_change_done')

@login_required
def profile_view(request):
    # Get teaching and learning skills with counts
    teaching_skills = request.user.userskill_set.filter(can_teach=True).select_related('skill')
    learning_skills = request.user.userskill_set.filter(wants_to_learn=True).select_related('skill')
    
    teaching_count = teaching_skills.count()
    learning_count = learning_skills.count()
    
    # Get exchange count (you might need to adjust this based on your model)
    exchange_count = SkillExchange.objects.filter(
        Q(mentor=request.user) | Q(learner=request.user)
    ).count()

    context = {
        'user': request.user,
        'teaching_skills': teaching_skills,
        'learning_skills': learning_skills,
        'teaching_count': teaching_count,
        'learning_count': learning_count,
        'exchange_count': exchange_count,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def public_profile_view(request, username):
    user = get_object_or_404(CustomUser, username=username)
    
    # Get user's teaching and learning skills with related skill details
    teaching_skills = UserSkill.objects.filter(
        user=user, 
        can_teach=True
    ).select_related('skill')
    
    learning_skills = UserSkill.objects.filter(
        user=user, 
        wants_to_learn=True
    ).select_related('skill')
    
    # ✅ New: Boolean to check if user has any teaching skills
    has_teaching_skills = teaching_skills.exists()

    context = {
        'profile_user': user,
        'teaching_skills': teaching_skills,
        'learning_skills': learning_skills,
        'has_teaching_skills': has_teaching_skills,  # <- Add this
    }
    return render(request, 'accounts/public_profile.html', context)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'accounts/profile_edit.html', {
        'form': form,
        'user': request.user
    })
@login_required
def availability_edit(request):
    if request.method == 'POST':
        form = AvailabilityForm(request.POST, user=request.user)
        if form.is_valid():
            # Delete existing availability
            request.user.availability.all().delete()
            
            # Create new availability slots
            for day in form.cleaned_data['days']:
                UserAvailability.objects.create(
                    user=request.user,
                    day=day,
                    start_time=form.cleaned_data['start_time'],
                    end_time=form.cleaned_data['end_time']
                )
            
            messages.success(request, 'Availability updated successfully!')
            return redirect('profile')
    else:
        form = AvailabilityForm(user=request.user)
    
    return render(request, 'accounts/availability_edit.html', {
        'form': form
    })




from django.views.generic import CreateView, UpdateView, ListView
from django.urls import reverse_lazy
from .models import Availability
from django.contrib.auth.mixins import LoginRequiredMixin

class AvailabilityUpdateView(LoginRequiredMixin, UpdateView):
    model = Availability
    fields = ['day', 'start_time', 'end_time']
    template_name = 'accounts/availability_form.html'
    success_url = reverse_lazy('dashboard')
    
    def get_object(self):
        # Get or create availability for the current user
        obj, created = Availability.objects.get_or_create(
            user=self.request.user,
            defaults={'day': 'mon', 'start_time': '09:00', 'end_time': '17:00'}
        )
        return obj

class AvailabilityListView(LoginRequiredMixin, ListView):
    model = Availability
    template_name = 'accounts/availability_list.html'
    
    def get_queryset(self):
        return Availability.objects.filter(user=self.request.user)