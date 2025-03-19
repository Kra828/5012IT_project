from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .forms import UserProfileForm, TeacherProfileForm, StudentProfileForm
from quizzes.models import QuizAttempt, Quiz
from courses.models import Course, Enrollment

# Try to import Submission model if it exists
try:
    from assignments.models import Submission
except ImportError:
    Submission = None

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
    """User Dashboard View"""
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_student():
            # Get courses the student is enrolled in
            # Get all published courses first
            all_courses = Course.objects.filter(is_published=True)
            enrollments = []
            
            # Ensure enrollment records exist for all courses and build the enrollment list
            for course in all_courses:
                enrollment, created = Enrollment.objects.get_or_create(
                    student=user,
                    course=course
                )
                
                # Calculate quiz completion progress
                total_quizzes = course.quizzes.count()
                completed_quizzes = QuizAttempt.objects.filter(
                    quiz__course=course,
                    student=user,
                    is_completed=True
                ).count()
                
                enrollment.quiz_progress = {
                    'total': total_quizzes,
                    'completed': completed_quizzes,
                    'percentage': round((completed_quizzes / total_quizzes * 100) if total_quizzes > 0 else 0, 1)
                }
                
                enrollments.append(enrollment)
            
            context['enrolled_courses'] = enrollments
            
            # Get quiz attempts count
            context['quiz_attempts'] = getattr(user, 'quiz_attempts', []).count() if hasattr(user, 'quiz_attempts') else 0
            # Get learning recommendations
            context['recommendations'] = getattr(user, 'learning_recommendations', []).filter(is_read=False)[:5] if hasattr(user, 'learning_recommendations') else []
            
            # Get average quiz score
            try:
                quiz_attempts = QuizAttempt.objects.filter(student=user, is_completed=True)
                if quiz_attempts.exists():
                    total_score = sum(attempt.score for attempt in quiz_attempts)
                    average_score = total_score / quiz_attempts.count()
                    context['average_quiz_score'] = round(average_score, 1)
                    # Get latest quiz attempt
                    context['latest_quiz_attempt'] = quiz_attempts.order_by('-completed_at').first()
                else:
                    context['average_quiz_score'] = 0
            except Exception as e:
                context['average_quiz_score'] = 0
                print(f"Error calculating quiz scores: {e}")
            
        elif user.is_teacher():
            # Get courses taught by the teacher
            # Ensure courses_taught is a QuerySet
            courses = user.courses_taught.all()
            context['courses_taught'] = courses
            
            # Get total number of students
            total_students = 0
            for course in courses:
                total_students += course.students.count()
            context['total_students'] = total_students
            
            # Get number of published quizzes
            try:
                published_quizzes = Quiz.objects.filter(
                    course__instructor=user,
                    is_published=True
                ).count()
            except:
                published_quizzes = 0
            context['published_quizzes'] = published_quizzes
            
        return context
