from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser,
    adding user type (student/teacher) and other necessary fields
    """
    USER_TYPE_CHOICES = (
        ('student', _('Student')),
        ('teacher', _('Teacher')),
    )
    
    # Set email to be unique
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='student',
        verbose_name=_('User Type')
    )
    bio = models.TextField(blank=True, verbose_name=_('Biography'))
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        verbose_name=_('Profile Picture')
    )
    date_of_birth = models.DateField(blank=True, null=True, verbose_name=_('Date of Birth'))
    
    # Teacher-specific fields
    specialization = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_('Specialization')
    )
    
    # Student-specific fields
    student_id = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name=_('Student ID')
    )
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def is_student(self):
        """Check if user is a student"""
        return self.user_type == 'student'
    
    def is_teacher(self):
        """Check if user is a teacher"""
        return self.user_type == 'teacher'
    
    def __str__(self):
        return self.email
