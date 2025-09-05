from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import AvailabilityUpdateView, AvailabilityListView

urlpatterns = [
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    
    # Availability
    path('availability/', AvailabilityUpdateView.as_view(), name='availability'),
    path('availability/list/', AvailabilityListView.as_view(), name='availability_list'),

    # Profile
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.public_profile_view, name='public_profile'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/availability/', views.availability_edit, name='availability_edit'),

    
    # Password Change
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    
    # Password Reset
    path('password/reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt'
    ), name='password_reset'),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]