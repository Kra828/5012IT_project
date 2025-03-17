import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elearning.settings')
django.setup()

from courses.models import Category

def create_subjects():
    """创建课程科目：英语、数学、物理"""
    subjects = [
        {
            'name': '英语',
            'slug': 'english',
            'description': '英语课程包括听力、口语、阅读和写作等全方位的语言技能训练。'
        },
        {
            'name': '数学',
            'slug': 'mathematics',
            'description': '数学课程涵盖代数、几何、微积分等数学基础知识和应用。'
        },
        {
            'name': '物理',
            'slug': 'physics',
            'description': '物理课程包括力学、电磁学、热学、光学等物理学基础知识和实验。'
        }
    ]
    
    for subject in subjects:
        category, created = Category.objects.get_or_create(
            slug=subject['slug'],
            defaults={
                'name': subject['name'],
                'description': subject['description']
            }
        )
        
        if created:
            print(f"创建了新科目: {subject['name']}")
        else:
            print(f"科目已存在: {subject['name']}")

if __name__ == '__main__':
    create_subjects()
    print("科目创建完成！") 