from django.urls import path
from . import views

app_name = 'courses'  # Namespace set

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('category/<int:category_id>/', views.courses_by_category, name='courses_by_category'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('create/', views.create_course, name='create'),  # ✅ FIXED this line
    path('manage/<int:course_id>/', views.manage_course, name='manage_course'),
    path('<int:pk>/', views.course_detail, name='detail'),
]
