from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, FileResponse
import os
from django.utils.text import slugify

from .models import Course, Chapter, Lesson, Enrollment, LessonProgress, CourseFile
from accounts.models import CustomUser

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        queryset = Course.objects.filter(is_published=True)
        # 移除按分类过滤的逻辑
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 移除基础课程自动创建的逻辑
        return context

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        context['chapters'] = course.chapters.all().order_by('order')
        
        # 添加最近发布的课程供相关课程使用
        context['recent_courses'] = Course.objects.filter(
            is_published=True
        ).exclude(id=course.id).order_by('-created_at')[:5]
        
        # 所有学生都被视为已注册
        if self.request.user.is_authenticated and self.request.user.is_student():
            context['is_enrolled'] = True
            
            # 确保学生已注册该课程
            Enrollment.objects.get_or_create(
                student=self.request.user,
                course=course
            )
        elif self.request.user.is_authenticated and self.request.user == course.instructor:
            context['is_enrolled'] = True
        else:
            context['is_enrolled'] = False
            
        return context

class ChapterListView(LoginRequiredMixin, ListView):
    model = Chapter
    template_name = 'courses/chapter_list.html'
    context_object_name = 'chapters'
    
    def get_queryset(self):
        course_slug = self.kwargs.get('course_slug')
        course = Course.objects.get(slug=course_slug)
        
        # 确保学生已注册该课程
        if self.request.user.is_student():
            Enrollment.objects.get_or_create(
                student=self.request.user,
                course=course
            )
            
        return Chapter.objects.filter(course=course).order_by('order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_slug = self.kwargs.get('course_slug')
        context['course'] = Course.objects.get(slug=course_slug)
        return context

class ChapterDetailView(LoginRequiredMixin, DetailView):
    model = Chapter
    template_name = 'courses/chapter_detail.html'
    context_object_name = 'chapter'
    pk_url_kwarg = 'chapter_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chapter = self.get_object()
        course = chapter.course
        
        # 确保学生已注册该课程
        if self.request.user.is_student():
            Enrollment.objects.get_or_create(
                student=self.request.user,
                course=course
            )
            
        context['course'] = course
        context['lessons'] = chapter.lessons.all().order_by('order')
        return context

class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'courses/lesson_detail.html'
    context_object_name = 'lesson'
    pk_url_kwarg = 'lesson_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.get_object()
        chapter = lesson.chapter
        course = chapter.course
        
        # 确保学生已注册该课程
        if self.request.user.is_student():
            Enrollment.objects.get_or_create(
                student=self.request.user,
                course=course
            )
            
        context['chapter'] = chapter
        context['course'] = course
        
        # 获取用户的观看进度
        if self.request.user.is_authenticated:
            progress, created = LessonProgress.objects.get_or_create(
                student=self.request.user,
                lesson=lesson
            )
            context['progress'] = progress
            
            # 获取下一课
            next_lesson = Lesson.objects.filter(
                chapter=chapter,
                order__gt=lesson.order
            ).order_by('order').first()
            
            if not next_lesson:
                # 如果当前章节没有下一课，查找下一章节的第一课
                next_chapter = Chapter.objects.filter(
                    course=chapter.course,
                    order__gt=chapter.order
                ).order_by('order').first()
                
                if next_chapter:
                    next_lesson = next_chapter.lessons.order_by('order').first()
            
            context['next_lesson'] = next_lesson
            
        return context

class EnrollCourseView(LoginRequiredMixin, View):
    def post(self, request, course_slug):
        course = Course.objects.get(slug=course_slug)
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course
        )
        return JsonResponse({'success': True, 'enrolled': True})
    
    def get(self, request, course_slug):
        # 自动注册所有课程
        if request.user.is_student():
            course = Course.objects.get(slug=course_slug)
            Enrollment.objects.get_or_create(
                student=request.user,
                course=course
            )
        return JsonResponse({'success': True, 'enrolled': True})

# 自动注册所有学生到所有课程的函数
def auto_enroll_all_students():
    students = CustomUser.objects.filter(user_type='student')
    courses = Course.objects.filter(is_published=True)
    
    for student in students:
        for course in courses:
            Enrollment.objects.get_or_create(
                student=student,
                course=course
            )
    
    return len(students) * len(courses)

class TeacherCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/teacher_course_list.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)

class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    template_name = 'courses/course_form.html'
    fields = ['title', 'overview', 'thumbnail']  # 移除category字段
    success_url = reverse_lazy('courses:teacher_course_list')
    
    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)

class CourseUpdateView(LoginRequiredMixin, UpdateView):
    model = Course
    template_name = 'courses/course_form.html'
    fields = ['title', 'overview', 'thumbnail', 'is_published']  # 移除category字段
    
    def get_success_url(self):
        return reverse_lazy('courses:course_detail', kwargs={'slug': self.object.slug})

class CourseDeleteView(LoginRequiredMixin, DeleteView):
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:teacher_course_list')

class ChapterCreateView(LoginRequiredMixin, CreateView):
    model = Chapter
    template_name = 'courses/chapter_form.html'
    fields = ['title', 'description', 'order']
    
    def form_valid(self, form):
        course_slug = self.kwargs.get('course_slug')
        form.instance.course = Course.objects.get(slug=course_slug)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('courses:chapter_list', kwargs={'course_slug': self.kwargs.get('course_slug')})

class ChapterUpdateView(LoginRequiredMixin, UpdateView):
    model = Chapter
    template_name = 'courses/chapter_form.html'
    fields = ['title', 'description', 'order']
    pk_url_kwarg = 'chapter_id'
    
    def get_success_url(self):
        return reverse_lazy('courses:chapter_detail', kwargs={
            'course_slug': self.kwargs.get('course_slug'),
            'chapter_id': self.object.id
        })

class ChapterDeleteView(LoginRequiredMixin, DeleteView):
    model = Chapter
    template_name = 'courses/chapter_confirm_delete.html'
    pk_url_kwarg = 'chapter_id'
    
    def get_success_url(self):
        return reverse_lazy('courses:chapter_list', kwargs={'course_slug': self.kwargs.get('course_slug')})

class LessonCreateView(LoginRequiredMixin, CreateView):
    model = Lesson
    template_name = 'courses/lesson_form.html'
    fields = ['title', 'video', 'content', 'duration', 'order']
    
    def form_valid(self, form):
        chapter_id = self.kwargs.get('chapter_id')
        form.instance.chapter = Chapter.objects.get(id=chapter_id)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('courses:chapter_detail', kwargs={
            'course_slug': self.kwargs.get('course_slug'),
            'chapter_id': self.kwargs.get('chapter_id')
        })

class LessonUpdateView(LoginRequiredMixin, UpdateView):
    model = Lesson
    template_name = 'courses/lesson_form.html'
    fields = ['title', 'video', 'content', 'duration', 'order']
    pk_url_kwarg = 'lesson_id'
    
    def get_success_url(self):
        return reverse_lazy('courses:lesson_detail', kwargs={
            'course_slug': self.kwargs.get('course_slug'),
            'chapter_id': self.kwargs.get('chapter_id'),
            'lesson_id': self.object.id
        })

class LessonDeleteView(LoginRequiredMixin, DeleteView):
    model = Lesson
    template_name = 'courses/lesson_confirm_delete.html'
    pk_url_kwarg = 'lesson_id'
    
    def get_success_url(self):
        return reverse_lazy('courses:chapter_detail', kwargs={
            'course_slug': self.kwargs.get('course_slug'),
            'chapter_id': self.kwargs.get('chapter_id')
        })

class CourseProgressView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/course_progress.html'
    context_object_name = 'course'
    
    def get_object(self):
        course_slug = self.kwargs.get('course_slug')
        return Course.objects.get(slug=course_slug)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()
        
        # 获取所有章节和课程
        chapters = course.chapters.all().order_by('order')
        context['chapters'] = chapters
        
        # 获取用户的学习进度
        if self.request.user.is_authenticated:
            progress_dict = {}
            for chapter in chapters:
                for lesson in chapter.lessons.all():
                    try:
                        progress = LessonProgress.objects.get(
                            student=self.request.user,
                            lesson=lesson
                        )
                        progress_dict[lesson.id] = progress
                    except LessonProgress.DoesNotExist:
                        progress_dict[lesson.id] = None
            
            context['progress_dict'] = progress_dict
            
        return context

class SaveLessonProgressView(LoginRequiredMixin, View):
    def post(self, request, course_slug, lesson_id):
        lesson = Lesson.objects.get(id=lesson_id)
        current_position = request.POST.get('current_position', 0)
        is_completed = request.POST.get('is_completed', False) == 'true'
        
        progress, created = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson
        )
        
        progress.current_position = current_position
        if is_completed:
            progress.is_completed = True
        progress.save()
        
        return JsonResponse({'success': True})

class CourseFileListView(LoginRequiredMixin, ListView):
    """课程文件列表视图"""
    model = CourseFile
    template_name = 'courses/course_file_list.html'
    context_object_name = 'files'
    
    def get_queryset(self):
        course_slug = self.kwargs.get('course_slug')
        course = Course.objects.get(slug=course_slug)
        return CourseFile.objects.filter(course=course)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = Course.objects.get(slug=self.kwargs['course_slug'])
        context['course'] = course
        
        # 确保教师或管理员可以上传和管理文件
        context['can_upload'] = (self.request.user.is_staff or 
                                self.request.user == course.instructor or
                                self.request.user.is_teacher())
        
        # 添加调试信息
        print(f"用户: {self.request.user.username}")
        print(f"是否是教师: {self.request.user.is_teacher()}")
        print(f"是否是课程教师: {self.request.user == course.instructor}")
        print(f"是否是管理员: {self.request.user.is_staff}")
        print(f"can_upload: {context['can_upload']}")
        
        return context

class CourseFileDeleteView(LoginRequiredMixin, DeleteView):
    """删除课程文件的视图"""
    model = CourseFile
    template_name = 'courses/course_file_confirm_delete.html'
    pk_url_kwarg = 'file_id'
    
    def get_success_url(self):
        return reverse_lazy('courses:course_files', kwargs={'course_slug': self.kwargs['course_slug']})
    
    def get_queryset(self):
        # 确保只有文件上传者、课程教师或管理员可以删除文件
        if self.request.user.is_staff:
            return CourseFile.objects.all()
        return CourseFile.objects.filter(uploaded_by=self.request.user)

class CourseFileDownloadView(LoginRequiredMixin, View):
    """下载课程文件的视图"""
    def get(self, request, course_slug, file_id):
        course_file = CourseFile.objects.get(id=file_id, course__slug=course_slug)
        
        # 所有登录用户都可以下载文件
        # 增加下载计数
        course_file.download_count += 1
        course_file.save()
        
        # 返回文件
        file_path = course_file.file.path
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response

class CourseFileUploadView(LoginRequiredMixin, CreateView):
    """教师上传课程文件的视图"""
    model = CourseFile
    template_name = 'courses/course_file_form.html'
    fields = ['title', 'description', 'file']
    
    def get_success_url(self):
        return reverse_lazy('courses:course_files', kwargs={'course_slug': self.kwargs['course_slug']})
    
    def form_valid(self, form):
        course = Course.objects.get(slug=self.kwargs['course_slug'])
        # 确保只有教师或管理员可以上传文件
        if not (self.request.user.is_staff or self.request.user == course.instructor or self.request.user.is_teacher()):
            return self.handle_no_permission()
            
        # 添加调试信息
        print(f"上传文件 - 用户: {self.request.user.username}")
        print(f"上传文件 - 是否是教师: {self.request.user.is_teacher()}")
        print(f"上传文件 - 是否是课程教师: {self.request.user == course.instructor}")
        print(f"上传文件 - 是否是管理员: {self.request.user.is_staff}")
        
        form.instance.course = course
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = Course.objects.get(slug=self.kwargs['course_slug'])
        return context
