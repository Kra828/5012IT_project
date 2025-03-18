from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from courses.models import Course
from accounts.models import CustomUser
from forum.models import DiscussionBoard
import random

class Command(BaseCommand):
    help = '创建示例课程'

    def handle(self, *args, **options):
        with transaction.atomic():
            # 获取管理员用户作为课程讲师
            admin = CustomUser.objects.filter(is_superuser=True).first()
            if not admin:
                self.stdout.write(self.style.ERROR('未找到管理员用户，请先创建一个管理员用户'))
                return
            
            # 创建三个基础课程：英语、数学、物理
            courses = [
                {'title': '英语', 'overview': '英语课程，包含听说读写训练'},
                {'title': '数学', 'overview': '数学课程，包含代数、几何和微积分'},
                {'title': '物理', 'overview': '物理课程，包含力学、电磁学和热学'}
            ]
            
            for course_data in courses:
                title = course_data['title']
                
                # 检查课程是否已存在
                if Course.objects.filter(title=title).exists():
                    course = Course.objects.get(title=title)
                    self.stdout.write(self.style.SUCCESS(f'课程 "{title}" 已存在'))
                    continue
                
                # 生成唯一的slug
                base_slug = slugify(title)
                slug = base_slug
                counter = 1
                
                while Course.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # 创建课程
                course = Course.objects.create(
                    title=title,
                    slug=slug,
                    instructor=admin,
                    overview=course_data['overview'],
                    is_published=True
                )
                
                # 为课程创建讨论区
                board, created = DiscussionBoard.objects.get_or_create(
                    title=f"{title}讨论区",
                    defaults={
                        'description': f"{title}课程的讨论区，欢迎提问和交流",
                        'course': course
                    }
                )
                
                self.stdout.write(self.style.SUCCESS(f'课程 "{title}" 创建成功'))
            
            self.stdout.write(self.style.SUCCESS('示例课程创建完成！')) 