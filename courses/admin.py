from django.contrib import admin
from .models import Course, Chapter, Lesson, CourseFile, LessonProgress
from accounts.models import CustomUser
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db import models

class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'overview', 'instructor__username')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ChapterInline]
    actions = ['publish_courses', 'unpublish_courses', 'assign_teacher']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # 限制instructor字段只显示teacher类型的用户
        if db_field.name == "instructor":
            kwargs["queryset"] = CustomUser.objects.filter(user_type='teacher')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def publish_courses(self, request, queryset):
        """发布选中的课程"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f'成功发布 {updated} 个课程', messages.SUCCESS)
    publish_courses.short_description = "发布选中的课程"
    
    def unpublish_courses(self, request, queryset):
        """取消发布选中的课程"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f'成功取消发布 {updated} 个课程', messages.SUCCESS)
    unpublish_courses.short_description = "取消发布选中的课程"
    
    def assign_teacher(self, request, queryset):
        """为选中的课程指派教师"""
        # 获取所有教师
        teachers = CustomUser.objects.filter(user_type='teacher')
        
        if not teachers.exists():
            self.message_user(request, '没有可用的教师用户', messages.ERROR)
            return
        
        # 获取没有教师的课程
        unassigned_courses = queryset.filter(instructor__isnull=True)
        
        if not unassigned_courses.exists():
            self.message_user(request, '选中的课程已经有教师', messages.WARNING)
            return
        
        # 为每个课程分配教师
        assigned_count = 0
        for course in unassigned_courses:
            # 找到负责课程最少的教师
            teacher = teachers.annotate(
                course_count=models.Count('course')
            ).order_by('course_count').first()
            
            course.instructor = teacher
            course.save()
            assigned_count += 1
        
        if assigned_count > 0:
            self.message_user(request, f'成功为 {assigned_count} 个课程分配教师', messages.SUCCESS)
        else:
            self.message_user(request, '没有为任何课程分配教师', messages.WARNING)
    assign_teacher.short_description = "为选中的课程指派教师"

@admin.register(CourseFile)
class CourseFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'uploaded_by', 'upload_date', 'download_count')
    list_filter = ('course', 'uploaded_by', 'upload_date')
    search_fields = ('title', 'description', 'course__title')
    date_hierarchy = 'upload_date'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # 限制course字段只显示已经有讲师的课程
        if db_field.name == "course":
            kwargs["queryset"] = Course.objects.filter(instructor__isnull=False)
        # 限制uploaded_by字段只显示教师类型的用户
        elif db_field.name == "uploaded_by":
            kwargs["queryset"] = CustomUser.objects.filter(user_type='teacher')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'duration', 'order')
    list_filter = ('chapter__course',)
    search_fields = ('title', 'content', 'chapter__title')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # 限制chapter字段只显示已经有课程的章节
        if db_field.name == "chapter":
            kwargs["queryset"] = Chapter.objects.filter(course__instructor__isnull=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'course__title')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # 限制course字段只显示已经有讲师的课程
        if db_field.name == "course":
            kwargs["queryset"] = Course.objects.filter(instructor__isnull=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# 取消注册不需要的模型或注册定制的Admin类
# admin.site.register(Chapter, ChapterAdmin)
# admin.site.register(Lesson, LessonAdmin)
# admin.site.register(LessonProgress)
