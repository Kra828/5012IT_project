# 在线学习平台

一个基于Django的在线学习平台，提供课程管理、视频学习、测验、作业、讨论区和AI助手等功能。

## 功能特点

### 用户管理
- 支持学生和教师两种用户类型
- 邮箱验证和密码找回
- 个人资料管理

### 课程管理
- 课程分类和搜索
- 课程详情页面
- 章节和视频管理
- 学习进度跟踪

### 测验和作业
- 多种题型（多选、判断、填空、论述）
- 自动评分系统
- 作业提交和教师评分

### 讨论区
- 课程讨论板
- 帖子、评论和回复
- 点赞和通知系统

### AI助手
- 基于ChatGPT或DeepSeek API的知识查询
- 个性化学习建议
- 学习进度跟踪和推荐

## 技术栈

- **后端**: Django 5.1
- **前端**: Bootstrap 5, jQuery
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **其他**: django-allauth, django-crispy-forms, django-ckeditor

## 安装和运行

### 环境要求
- Python 3.8+
- pip

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/online_learning_platform.git
cd online_learning_platform
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 数据库迁移
```bash
python manage.py migrate
```

5. 创建超级用户
```bash
python manage.py createsuperuser
```

6. 运行开发服务器
```bash
python manage.py runserver
```

7. 访问网站
- 前台: http://127.0.0.1:8000/
- 管理后台: http://127.0.0.1:8000/admin/

## 项目结构

```
online_learning_platform/
├── accounts/            # 用户账户应用
├── courses/             # 课程管理应用
├── quizzes/             # 测验和作业应用
├── forum/               # 讨论区应用
├── ai_assistant/        # AI助手应用
├── elearning/           # 项目配置
├── templates/           # HTML模板
├── static/              # 静态文件
├── media/               # 用户上传的媒体文件
├── manage.py            # Django管理脚本
└── requirements.txt     # 项目依赖
```

## 配置AI助手

要使用AI助手功能，您需要配置API密钥：

1. 创建`.env`文件在项目根目录
2. 添加您的API密钥：
```
OPENAI_API_KEY=your_openai_api_key
# 或者
DEEPSEEK_API_KEY=your_deepseek_api_key
```

## 生产环境部署

对于生产环境，请确保：

1. 设置`DEBUG=False`
2. 使用更安全的密钥
3. 配置适当的数据库（如PostgreSQL）
4. 设置SMTP邮件服务
5. 使用HTTPS
6. 配置静态文件服务

## 贡献

欢迎贡献代码、报告问题或提出改进建议。

## 许可证

本项目采用MIT许可证。