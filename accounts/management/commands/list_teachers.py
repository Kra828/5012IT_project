from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from courses.models import Course
from django.db.models import Count

class Command(BaseCommand):
    help = '列出所有教师和他们负责的课程'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='显示所有用户，包括学生')

    def handle(self, *args, **options):
        show_all = options.get('all', False)
        
        if show_all:
            users = CustomUser.objects.all().order_by('user_type', 'username')
        else:
            users = CustomUser.objects.filter(user_type='teacher').order_by('username')
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('没有找到教师'))
            return
        
        self.stdout.write(self.style.SUCCESS('用户列表:'))
        self.stdout.write('=' * 80)
        
        for user in users:
            courses = Course.objects.filter(instructor=user)
            role = '教师' if user.user_type == 'teacher' else '学生'
            
            self.stdout.write(f'用户名: {user.username}')
            self.stdout.write(f'角色: {role}')
            self.stdout.write(f'邮箱: {user.email}')
            
            if user.user_type == 'teacher':
                self.stdout.write(f'负责课程数: {courses.count()}')
                if courses.exists():
                    self.stdout.write('负责的课程:')
                    for course in courses:
                        self.stdout.write(f'  - {course.title}')
                else:
                    self.stdout.write('暂无负责的课程')
            
            self.stdout.write('-' * 80) 