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
    
    actions = ['make_teacher', 'make_student']
    
    def make_teacher(self, request, queryset):
        """Set selected users as teachers"""
        updated = queryset.update(user_type='teacher')
        self.message_user(request, f'Successfully set {updated} users as teachers', messages.SUCCESS)
    make_teacher.short_description = "Set selected users as teachers"
    
    def make_student(self, request, queryset):
        """Set selected users as students"""
        updated = queryset.update(user_type='student')
        self.message_user(request, f'Successfully set {updated} users as students', messages.SUCCESS)
    make_student.short_description = "Set selected users as students"

# Register the CustomUser model with the custom admin
admin.site.register(CustomUser, CustomUserAdmin)

# Unregister the Group model since it's not being used
admin.site.unregister(Group)

# Unregister the Permission model if you want to hide it as well
try:
    admin.site.unregister(Permission)
except admin.sites.NotRegistered:
    pass
