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
        # Limit instructor field to show only users with teacher type
        if db_field.name == "instructor":
            kwargs["queryset"] = CustomUser.objects.filter(user_type='teacher')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def publish_courses(self, request, queryset):
        """Publish selected courses"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f'Successfully published {updated} courses', messages.SUCCESS)
    publish_courses.short_description = "Publish selected courses"
    
    def unpublish_courses(self, request, queryset):
        """Unpublish selected courses"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f'Successfully unpublished {updated} courses', messages.SUCCESS)
    unpublish_courses.short_description = "Unpublish selected courses"
    
    def assign_teacher(self, request, queryset):
        """Assign teachers to selected courses"""
        # Get all teachers
        teachers = CustomUser.objects.filter(user_type='teacher')
        
        if not teachers.exists():
            self.message_user(request, 'No teacher users available', messages.ERROR)
            return
        
        # Get courses without instructors
        unassigned_courses = queryset.filter(instructor__isnull=True)
        
        if not unassigned_courses.exists():
            self.message_user(request, 'Selected courses already have instructors', messages.WARNING)
            return
        
        # Assign teachers to each course
        assigned_count = 0
        for course in unassigned_courses:
            # Find the teacher with the fewest courses
            teacher = teachers.annotate(
                course_count=models.Count('course')
            ).order_by('course_count').first()
            
            course.instructor = teacher
            course.save()
            assigned_count += 1
        
        if assigned_count > 0:
            self.message_user(request, f'Successfully assigned instructors to {assigned_count} courses', messages.SUCCESS)
        else:
            self.message_user(request, 'No courses were assigned to any instructors', messages.WARNING)
    assign_teacher.short_description = "Assign teachers to selected courses"

@admin.register(CourseFile)
class CourseFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'uploaded_by', 'upload_date', 'download_count')
    list_filter = ('course', 'uploaded_by', 'upload_date')
    search_fields = ('title', 'description', 'course__title')
    date_hierarchy = 'upload_date'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Limit course field to show only courses with instructors
        if db_field.name == "course":
            kwargs["queryset"] = Course.objects.filter(instructor__isnull=False)
        # Limit uploaded_by field to show only teacher users
        elif db_field.name == "uploaded_by":
            kwargs["queryset"] = CustomUser.objects.filter(user_type='teacher')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'duration', 'order')
    list_filter = ('chapter__course',)
    search_fields = ('title', 'content', 'chapter__title')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Limit chapter field to show only chapters with courses
        if db_field.name == "chapter":
            kwargs["queryset"] = Chapter.objects.filter(course__instructor__isnull=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'course__title')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Limit course field to show only courses with instructors
        if db_field.name == "course":
            kwargs["queryset"] = Course.objects.filter(instructor__isnull=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# 取消注册不需要的模型或注册定制的Admin类
# admin.site.register(Chapter, ChapterAdmin)
# admin.site.register(Lesson, LessonAdmin)
# admin.site.register(LessonProgress)
