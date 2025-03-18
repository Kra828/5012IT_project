from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    # 测验列表视图
    path('', views.QuizListView.as_view(), name='quiz_list'),
    
    # 教师测验管理
    path('teacher/', views.TeacherQuizListView.as_view(), name='teacher_quiz_list'),
    path('create/', views.QuizCreateView.as_view(), name='quiz_create'),
    path('manage/<int:quiz_id>/edit/', views.QuizUpdateView.as_view(), name='quiz_edit'),
    path('manage/<int:quiz_id>/delete/', views.QuizDeleteView.as_view(), name='quiz_delete'),
    
    # 测验详情和尝试
    path('<int:quiz_id>/', views.QuizDetailView.as_view(), name='quiz_detail'),
    path('<int:quiz_id>/attempt/', views.QuizAttemptView.as_view(), name='quiz_attempt'),
    path('result/<int:attempt_id>/', views.QuizResultView.as_view(), name='quiz_result'),
    
    # 问题管理
    path('manage/<int:quiz_id>/questions/', views.QuestionListView.as_view(), name='question_list'),
    path('manage/<int:quiz_id>/questions/create/', views.QuestionCreateView.as_view(), name='question_create'),
    path('manage/<int:quiz_id>/questions/<int:question_id>/edit/', 
         views.QuestionUpdateView.as_view(), name='question_update'),
    path('manage/<int:quiz_id>/questions/<int:question_id>/delete/', 
         views.QuestionDeleteView.as_view(), name='question_delete'),
    
    # 作业
    path('assignments/', views.AssignmentListView.as_view(), name='assignment_list'),
    path('assignments/<int:assignment_id>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<int:assignment_id>/submit/', views.SubmitAssignmentView.as_view(), name='submit_assignment'),
    
    # 教师作业管理
    path('assignments/manage/', views.TeacherAssignmentListView.as_view(), name='teacher_assignment_list'),
    path('assignments/manage/create/', views.AssignmentCreateView.as_view(), name='assignment_create'),
    path('assignments/manage/<int:assignment_id>/edit/', 
         views.AssignmentUpdateView.as_view(), name='assignment_update'),
    path('assignments/manage/<int:assignment_id>/delete/', 
         views.AssignmentDeleteView.as_view(), name='assignment_delete'),
    path('assignments/manage/<int:assignment_id>/submissions/', 
         views.AssignmentSubmissionListView.as_view(), name='assignment_submission_list'),
    path('assignments/manage/<int:assignment_id>/submissions/<int:submission_id>/', 
         views.GradeSubmissionView.as_view(), name='grade_submission'),
] 