from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .forms import UserProfileForm, TeacherProfileForm, StudentProfileForm
from quizzes.models import QuizAttempt

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
    success_url = reverse_lazy('dashboard')
    fields = ['first_name', 'last_name', 'username', 'email', 'date_of_birth', 'bio', 'profile_picture']
    
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
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_student():
            # 获取学生已注册的课程
            enrolled_courses = user.enrollments.all()
            context['enrolled_courses'] = enrolled_courses
            
            # 为每个课程计算测验完成进度
            for enrollment in enrolled_courses:
                total_quizzes = enrollment.course.quizzes.count()
                completed_quizzes = QuizAttempt.objects.filter(
                    quiz__course=enrollment.course,
                    student=user,
                    is_completed=True
                ).count()
                enrollment.quiz_progress = {
                    'total': total_quizzes,
                    'completed': completed_quizzes,
                    'percentage': round((completed_quizzes / total_quizzes * 100) if total_quizzes > 0 else 0, 1)
                }
            
            # 获取测验尝试次数
            context['quiz_attempts'] = getattr(user, 'quiz_attempts', []).count() if hasattr(user, 'quiz_attempts') else 0
            # 获取学习推荐
            context['recommendations'] = getattr(user, 'learning_recommendations', []).filter(is_read=False)[:5] if hasattr(user, 'learning_recommendations') else []
            
            # 获取平均测验得分
            try:
                quiz_attempts = QuizAttempt.objects.filter(student=user, is_completed=True)
                if quiz_attempts.exists():
                    total_score = sum(attempt.score for attempt in quiz_attempts)
                    average_score = total_score / quiz_attempts.count()
                    context['average_quiz_score'] = round(average_score, 1)
                    # 获取最近的测验尝试
                    context['latest_quiz_attempt'] = quiz_attempts.order_by('-completed_at').first()
                else:
                    context['average_quiz_score'] = 0
            except Exception as e:
                context['average_quiz_score'] = 0
                print(f"Error calculating quiz scores: {e}")
            
        elif user.is_teacher():
            # 获取教师教授的课程
            # 确保courses_taught是QuerySet对象
            courses = user.courses_taught.all()
            context['courses_taught'] = courses
            
            # 获取学生总数
            total_students = 0
            for course in courses:
                total_students += course.students.count()
            context['total_students'] = total_students
            
            # 获取待评阅的作业数量
            try:
                pending_submissions = Submission.objects.filter(
                    assignment__course__instructor=user,
                    status='submitted'
                ).count()
            except:
                pending_submissions = 0
            context['pending_submissions'] = pending_submissions
            
        return context
