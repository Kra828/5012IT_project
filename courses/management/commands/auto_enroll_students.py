from django.core.management.base import BaseCommand
from django.db import transaction
from courses.models import Course, Enrollment
from accounts.models import CustomUser

class Command(BaseCommand):
    help = '自动将所有学生注册到所有课程'

    def handle(self, *args, **options):
        with transaction.atomic():
            students = CustomUser.objects.filter(user_type='student')
            courses = Course.objects.filter(is_published=True)
            
            self.stdout.write(self.style.SUCCESS(f'找到 {students.count()} 名学生和 {courses.count()} 门课程'))
            
            enrollment_count = 0
            for student in students:
                for course in courses:
                    enrollment, created = Enrollment.objects.get_or_create(
                        student=student,
                        course=course
                    )
                    if created:
                        enrollment_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'成功创建 {enrollment_count} 条新的注册记录')) 