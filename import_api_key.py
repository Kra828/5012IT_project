#!/usr/bin/env python
"""
将.env文件中的OpenAI API密钥导入到数据库中
"""
import os
import django
import sys
from pathlib import Path
from dotenv import load_dotenv

# 设置Django环境
sys.path.append(str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elearning.settings')
django.setup()

# 导入模型
from ai_assistant.models import OpenAISettings

def import_api_key():
    """从.env文件导入API密钥到数据库"""
    # 加载.env文件
    load_dotenv()
    
    # 获取API密钥
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("错误：在.env文件中未找到OPENAI_API_KEY")
        return
    
    # 检查是否已存在活跃的API密钥
    existing_active = OpenAISettings.objects.filter(is_active=True).first()
    
    if existing_active:
        print(f"已存在活跃的API密钥：{existing_active.api_key_name}")
        choice = input("是否要替换现有的活跃API密钥？(y/n): ")
        if choice.lower() != 'y':
            print("操作已取消")
            return
    
    # 创建新的API密钥设置
    api_settings = OpenAISettings(
        api_key_name="环境变量导入的API密钥",
        api_key=api_key,
        is_active=True
    )
    api_settings.save()
    
    print(f"API密钥已成功导入到数据库，名称为：{api_settings.api_key_name}")
    print("您现在可以通过管理界面管理此API密钥")

if __name__ == "__main__":
    import_api_key() 