from django.urls import path
from . import views  # Import the views module

app_name = 'skills'

urlpatterns = [
    path('', views.discover_skills, name='discover'),
    path('categories/', views.skill_categories, name='categories'),
    path('category/<int:category_id>/', views.skill_category_detail, name='category_detail'),
    path('add/', views.add_skill, name='add_skill'),
    path('add/teaching/', views.add_skill, {'skill_type': 'teaching'}, name='add_teaching_skill'),
    path('add/learning/', views.add_skill, {'skill_type': 'learning'}, name='add_learning_skill'),
    path('edit/<int:skill_id>/', views.edit_skill, name='edit_skill'),
    path('remove/<int:skill_id>/', views.remove_skill, name='remove_skill'),
    path('skill/<int:skill_id>/mentors/', views.find_mentors, name='find_mentors'),
    path('skill/<int:skill_id>/learners/', views.find_learners, name='find_learners'),
    path('exchange/<int:user_id>/<int:skill_id>/', views.initiate_exchange, name='initiate_exchange'),
    path('exchange/<int:exchange_id>/', views.exchange_detail, name='exchange_detail'),
    path('exchange/<int:exchange_id>/accept/', views.accept_exchange, name='accept_exchange'),
    path('exchange/<int:exchange_id>/reject/', views.reject_exchange, name='reject_exchange'),
    path('exchange/<int:exchange_id>/complete/', views.complete_exchange, name='complete_exchange'),
    path('exchange/<int:exchange_id>/review/', views.submit_review, name='submit_review'),
    path('schedule/', views.schedule_exchange, name='schedule'),
    path('schedule/<int:skill_id>/', views.schedule_exchange, name='schedule_exchange'),
    path('my-exchanges/', views.my_exchanges, name='my_exchanges'),
    path('add/', views.add_skill, name='add'),
    path('discover-users/', views.discover_users, name='discover_users'),  # New URL pattern
    path('send-request/<str:username>/', views.send_skill_request, name='send_request'),
    path('manage-request/<int:request_id>/<str:action>/', views.manage_request, name='manage_request'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('room/<str:room_id>/', views.communication_room, name='communication_room'),
    path('send-request/<str:username>/', views.send_skill_request, name='send_request'),
    path('requests/', views.view_requests, name='view_requests'),
    path('handle-request/<int:request_id>/<str:action>/', views.handle_request, name='handle_request'),
    path('send-request/<str:username>/', views.send_skill_request, name='send_request'),
    path('requests/<int:request_id>/accept/', views.accept_request, name='accept_request'),
    path('communication/<int:request_id>/', views.communication_room, name='communication_room'),
    path('requests/reject/<int:request_id>/', views.reject_request, name='reject_request'),
    path('edit/<int:skill_id>/', views.edit_skill, name='edit'),
    
    
]