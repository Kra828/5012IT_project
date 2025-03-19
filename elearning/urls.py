"""
URL configuration for elearning project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from accounts.views import DashboardView

# Customize admin interface
admin.site.site_header = "Smart Interactive Learning Platform Administration"
admin.site.site_title = "Smart Interactive Learning Platform Admin"
admin.site.index_title = "Admin Dashboard"

# Unregister unnecessary models
try:
    # Unregister social account related models
    from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
    from allauth.account.models import EmailAddress
    
    admin.site.unregister(SocialAccount)
    admin.site.unregister(SocialApp)
    admin.site.unregister(SocialToken)
    admin.site.unregister(EmailAddress)
    
    # Unregister unnecessary course related models
    from courses.models import Chapter, Lesson, LessonProgress
    
    admin.site.unregister(Chapter)
    admin.site.unregister(Lesson)
    admin.site.unregister(LessonProgress)
    
    # Unregister unnecessary AI assistant models
    from ai_assistant.models import AIChat, ChatMessage, LearningRecommendation, LearningProgress
    
    try:
        admin.site.unregister(AIChat)
        admin.site.unregister(ChatMessage)
        admin.site.unregister(LearningRecommendation)
        admin.site.unregister(LearningProgress)
    except:
        pass
except:
    pass

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # User authentication
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    
    # Application URLs
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('courses/', include('courses.urls')),
    path('quizzes/', include('quizzes.urls')),
    path('forum/', include('forum.urls')),
    path('ai-assistant/', include('ai_assistant.urls')),
    
    # CKEditor
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

# Serve media files in development environment
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
