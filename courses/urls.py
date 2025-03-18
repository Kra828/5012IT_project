from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # 课程列表和详情
    path('', views.CourseListView.as_view(), name='course_list'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    
    # 课程文件
    path('<slug:course_slug>/files/', views.CourseFileListView.as_view(), name='course_files'),
    path('<slug:course_slug>/files/upload/', views.CourseFileUploadView.as_view(), name='course_file_upload'),
    path('<slug:course_slug>/files/<int:file_id>/download/', views.CourseFileDownloadView.as_view(), name='course_file_download'),
    path('<slug:course_slug>/files/<int:file_id>/delete/', views.CourseFileDeleteView.as_view(), name='course_file_delete'),
    
    # 课程章节和课时
    path('<slug:course_slug>/chapters/', views.ChapterListView.as_view(), name='chapter_list'),
    path('<slug:course_slug>/chapters/<int:chapter_id>/', views.ChapterDetailView.as_view(), name='chapter_detail'),
    path('<slug:course_slug>/chapters/<int:chapter_id>/lessons/<int:lesson_id>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    
    # 课程进度
    path('<slug:course_slug>/progress/', views.CourseProgressView.as_view(), name='course_progress'),
    path('<slug:course_slug>/lessons/<int:lesson_id>/progress/', views.SaveLessonProgressView.as_view(), name='save_lesson_progress'),
    
    # 课程注册
    path('<slug:course_slug>/enroll/', views.EnrollCourseView.as_view(), name='enroll_course'),
    
    # 教师课程管理
    path('manage/', views.TeacherCourseListView.as_view(), name='teacher_course_list'),
    # 仅管理员可以创建和删除课程
    # path('manage/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('manage/<slug:slug>/update/', views.CourseUpdateView.as_view(), name='course_update'),
    # path('manage/<slug:slug>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    
    # 章节管理
    path('<slug:course_slug>/chapters/create/', views.ChapterCreateView.as_view(), name='chapter_create'),
    path('<slug:course_slug>/chapters/<int:chapter_id>/update/', views.ChapterUpdateView.as_view(), name='chapter_update'),
    path('<slug:course_slug>/chapters/<int:chapter_id>/delete/', views.ChapterDeleteView.as_view(), name='chapter_delete'),
    
    # 课时管理
    path('<slug:course_slug>/chapters/<int:chapter_id>/lessons/create/', views.LessonCreateView.as_view(), name='lesson_create'),
    path('<slug:course_slug>/chapters/<int:chapter_id>/lessons/<int:lesson_id>/update/', views.LessonUpdateView.as_view(), name='lesson_update'),
    path('<slug:course_slug>/chapters/<int:chapter_id>/lessons/<int:lesson_id>/delete/', views.LessonDeleteView.as_view(), name='lesson_delete'),
] 