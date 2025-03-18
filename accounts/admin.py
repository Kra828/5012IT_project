from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from .models import CustomUser
from courses.models import Course
from .forms import UserProfileForm

class CustomUserAdmin(UserAdmin):
    """Custom User Admin that simplifies the interface"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'profile_picture', 
                                        'date_of_birth', 'bio')}),
        (_('User type'), {'fields': ('user_type',)}),
        (_('Status'), {'fields': ('is_active',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        
        # Only show is_staff and is_superuser fields to superusers
        if not is_superuser:
            if 'is_staff' in form.base_fields:
                form.base_fields['is_staff'].disabled = True
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
                
        return form
    
    actions = ['make_teacher', 'make_student', 'assign_courses']
    
    def make_teacher(self, request, queryset):
        """将选中的用户设置为教师"""
        updated = queryset.update(user_type='teacher')
        self.message_user(request, f'成功将 {updated} 个用户设置为教师', messages.SUCCESS)
    make_teacher.short_description = "将选中的用户设置为教师"
    
    def make_student(self, request, queryset):
        """将选中的用户设置为学生"""
        updated = queryset.update(user_type='student')
        self.message_user(request, f'成功将 {updated} 个用户设置为学生', messages.SUCCESS)
    make_student.short_description = "将选中的用户设置为学生"
    
    def assign_courses(self, request, queryset):
        """为选中的教师分配课程"""
        teachers = queryset.filter(user_type='teacher')
        if not teachers.exists():
            self.message_user(request, '请选择至少一个教师用户', messages.ERROR)
            return
        
        # 获取没有教师的课程
        unassigned_courses = Course.objects.filter(instructor__isnull=True)
        
        if not unassigned_courses.exists():
            self.message_user(request, '没有未分配的课程', messages.WARNING)
            return
        
        # 为每个教师分配课程
        assigned_count = 0
        for teacher in teachers:
            # 获取该教师已经负责的课程数量
            teacher_courses_count = Course.objects.filter(instructor=teacher).count()
            
            # 如果教师已经有课程，跳过
            if teacher_courses_count > 0:
                continue
            
            # 获取一个未分配的课程
            if unassigned_courses.exists():
                course = unassigned_courses.first()
                course.instructor = teacher
                course.save()
                unassigned_courses = unassigned_courses.exclude(id=course.id)
                assigned_count += 1
        
        if assigned_count > 0:
            self.message_user(request, f'成功为 {assigned_count} 个教师分配课程', messages.SUCCESS)
        else:
            self.message_user(request, '没有为任何教师分配课程', messages.WARNING)
    assign_courses.short_description = "为选中的教师分配课程"

# Register the CustomUser model with the custom admin
admin.site.register(CustomUser, CustomUserAdmin)

# Unregister the Group model since it's not being used
admin.site.unregister(Group)

# Unregister the Permission model if you want to hide it as well
try:
    admin.site.unregister(Permission)
except admin.sites.NotRegistered:
    pass
