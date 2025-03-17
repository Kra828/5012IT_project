from django.core.management.base import BaseCommand, CommandError
from accounts.models import CustomUser
from courses.models import Course
from django.db.models import Q

class Command(BaseCommand):
    help = '指派用户为教师并分配课程'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='要指派为教师的用户名')
        parser.add_argument('--course', type=str, help='要分配给教师的课程标题（可选）')

    def handle(self, *args, **options):
        username = options['username']
        course_title = options.get('course')
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            raise CommandError(f'用户 "{username}" 不存在')
        
        # 将用户设置为教师
        if user.user_type == 'teacher':
            self.stdout.write(self.style.WARNING(f'用户 "{username}" 已经是教师'))
        else:
            user.user_type = 'teacher'
            user.save()
            self.stdout.write(self.style.SUCCESS(f'成功将用户 "{username}" 指派为教师'))
        
        # 如果指定了课程，将该课程分配给教师
        if course_title:
            try:
                course = Course.objects.get(Q(title=course_title) | Q(slug=course_title))
                course.instructor = user
                course.save()
                self.stdout.write(self.style.SUCCESS(f'成功将课程 "{course.title}" 分配给教师 "{username}"'))
            except Course.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'课程 "{course_title}" 不存在'))
            except Course.MultipleObjectsReturned:
                self.stdout.write(self.style.ERROR(f'存在多个标题为 "{course_title}" 的课程，请使用更具体的标题'))
        
        # 显示该教师负责的所有课程
        courses = Course.objects.filter(instructor=user)
        if courses.exists():
            self.stdout.write(self.style.SUCCESS(f'教师 "{username}" 负责的课程:'))
            for course in courses:
                self.stdout.write(f'  - {course.title}')
        else:
            self.stdout.write(self.style.WARNING(f'教师 "{username}" 目前没有负责任何课程')) 