from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    """
    自定义用户模型，扩展Django的AbstractUser，
    添加用户类型（学生/教师）和其他必要字段
    """
    USER_TYPE_CHOICES = (
        ('student', _('Student')),
        ('teacher', _('Teacher')),
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
    
    # 教师特有字段
    specialization = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_('Specialization')
    )
    
    # 学生特有字段
    student_id = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name=_('Student ID')
    )
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def is_student(self):
        """检查用户是否为学生"""
        return self.user_type == 'student'
    
    def is_teacher(self):
        """检查用户是否为教师"""
        return self.user_type == 'teacher'
    
    def __str__(self):
        return self.email
