from django.core.management.base import BaseCommand
from courses.models import Course
from forum.models import DiscussionBoard

class Command(BaseCommand):
    help = '为所有课程创建讨论区'

    def handle(self, *args, **options):
        courses = Course.objects.all()
        created_count = 0
        
        for course in courses:
            if not hasattr(course, 'discussion_board') or course.discussion_board is None:
                board = DiscussionBoard.objects.create(
                    course=course,
                    description=f"{course.title}的讨论区，欢迎所有学生和教师参与讨论。"
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'为课程 "{course.title}" 创建了讨论区'))
        
        if created_count == 0:
            self.stdout.write(self.style.WARNING('所有课程已有讨论区，无需创建'))
        else:
            self.stdout.write(self.style.SUCCESS(f'成功创建了 {created_count} 个讨论区')) 