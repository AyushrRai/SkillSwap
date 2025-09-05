from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='list'),  # Using 'list' as primary name
    path('', views.project_list, name='project_list'),
    # Other URL patterns remain the same
    path('create/', views.create_project, name='create_project'),
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('<int:project_id>/', views.project_detail, name='detail'),
    path('<int:project_id>/tasks/<int:task_id>/', views.manage_task, name='manage_task'),
    path('projects/<int:project_id>/tasks/<int:task_id>/', views.manage_task, name='manage_task'),
    path('<int:project_id>/tasks/add/', views.add_task, name='add_task'),
    path('<int:project_id>/invite/', views.invite_member, name='invite_member'),
    path('<int:pk>/join/', views.join_project, name='join'),

]