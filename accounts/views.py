from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .forms import UserProfileForm, TeacherProfileForm, StudentProfileForm

User = get_user_model()

class ProfileView(LoginRequiredMixin, DetailView):
    """用户个人资料视图"""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self, queryset=None):
        return self.request.user

class UpdateProfileView(LoginRequiredMixin, UpdateView):
    """更新用户个人资料视图"""
    model = User
    template_name = 'accounts/update_profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_form_class(self):
        """根据用户类型返回不同的表单"""
        if self.request.user.is_teacher():
            return TeacherProfileForm
        else:
            return StudentProfileForm
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _('Your profile has been updated successfully.'))
        return super().form_valid(form)

class DashboardView(LoginRequiredMixin, TemplateView):
    """用户仪表盘视图"""
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_student():
            # 获取学生已注册的课程
            context['enrolled_courses'] = user.courses_enrolled.all()
            # 获取最近的测验尝试
            context['recent_quiz_attempts'] = user.quiz_attempts.order_by('-started_at')[:5]
            # 获取最近的作业提交
            context['recent_submissions'] = user.submissions.order_by('-submitted_at')[:5]
            # 获取学习推荐
            context['recommendations'] = user.learning_recommendations.filter(is_read=False)[:5]
            
        elif user.is_teacher():
            # 获取教师创建的课程
            context['courses_taught'] = user.courses_taught.all()
            # 获取最近的作业提交（需要评分的）
            from quizzes.models import Submission
            context['pending_submissions'] = Submission.objects.filter(
                assignment__course__instructor=user,
                status='submitted'
            ).order_by('-submitted_at')[:10]
            
        return context
