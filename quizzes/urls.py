from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    # 测验
    path('', views.QuizListView.as_view(), name='quiz_list'),
    path('<int:quiz_id>/', views.QuizDetailView.as_view(), name='quiz_detail'),
    path('<int:quiz_id>/start/', views.StartQuizView.as_view(), name='start_quiz'),
    path('<int:quiz_id>/attempt/<int:attempt_id>/', views.QuizAttemptView.as_view(), name='quiz_attempt'),
    path('<int:quiz_id>/attempt/<int:attempt_id>/submit/', views.SubmitQuizView.as_view(), name='submit_quiz'),
    path('<int:quiz_id>/attempt/<int:attempt_id>/results/', views.QuizResultsView.as_view(), name='quiz_results'),
    
    # 教师测验管理
    path('manage/', views.TeacherQuizListView.as_view(), name='teacher_quiz_list'),
    path('manage/create/', views.QuizCreateView.as_view(), name='quiz_create'),
    path('manage/<int:quiz_id>/edit/', views.QuizUpdateView.as_view(), name='quiz_update'),
    path('manage/<int:quiz_id>/delete/', views.QuizDeleteView.as_view(), name='quiz_delete'),
    path('manage/<int:quiz_id>/publish/', views.PublishQuizView.as_view(), name='publish_quiz'),
    
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