from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    # AI Assistant Homepage
    path('', views.AIAssistantHomeView.as_view(), name='home'),
    
    # API Interface
    path('api/query/', views.AIQueryAPIView.as_view(), name='ai_query_api'),
] 