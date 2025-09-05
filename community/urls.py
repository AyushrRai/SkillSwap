# urls.py
from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # Circles
    path('', views.circle_list, name='circle_list'),
    path('create/', views.create_circle, name='create_circle'),
    path('<int:circle_id>/', views.circle_detail, name='circle_detail'),
    path('<int:circle_id>/edit/', views.edit_circle, name='edit_circle'),
    path('<int:circle_id>/leave/', views.leave_circle, name='leave_circle'),
    path('<int:circle_id>/members/', views.circle_members, name='circle_members'),
    path('<int:circle_id>/resources/', views.circle_resources, name='circle_resources'),
    path('<int:circle_id>/requests/', views.manage_requests, name='manage_requests'),
    path('<int:circle_id>/invite/', views.invite_member, name='invite_member'),
    
    # Posts
    path('<int:circle_id>/post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    
    # Events
    path('<int:circle_id>/events/create/', views.create_event, name='create_event'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    
]