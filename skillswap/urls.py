from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    
    # Authentication
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    
    # Apps with namespaces
    path('skills/', include(('skills.urls', 'skills'), namespace='skills')),
    #path('skills/', include(('skills.urls', 'skills'), namespace='skills')),
    path('community/', include(('community.urls', 'community'), namespace='community')),
    path('courses/', include(('courses.urls', 'courses'), namespace='courses')),
    path('projects/', include(('projects.urls', 'projects'), namespace='projects')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)