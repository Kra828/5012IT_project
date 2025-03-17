from django.contrib import admin
from django.apps import apps

# 隐藏不需要的应用和模型
admin.site.site_header = "在线学习平台管理"
admin.site.site_title = "在线学习平台管理"
admin.site.index_title = "管理面板"

# 要隐藏的应用
HIDDEN_APPS = [
    # 社交账户相关
    'allauth.socialaccount',  # 社交账户
    'socialaccount',          # 社交账户
    'allauth.account',        # 账户管理
    'account',                # 账户管理
]

# 要隐藏的模型
HIDDEN_MODELS = [
    'courses.Chapter',
    'courses.Lesson',
    'courses.LessonProgress',
    'socialaccount.SocialAccount',
    'socialaccount.SocialApp',
    'socialaccount.SocialToken',
]

# 隐藏指定的应用和模型
for app_label, model_dict in admin.site._registry.copy().items():
    app_config = apps.get_app_config(app_label.split('.')[0])
    app_name = app_config.label
    
    # 隐藏整个应用
    if any(app_name == hidden_app.split('.')[-1] for hidden_app in HIDDEN_APPS):
        try:
            admin.site.unregister(model_dict.model)
        except:
            pass
        continue
    
    # 隐藏特定模型
    model_name = f"{app_name}.{model_dict.model.__name__}"
    if any(model_name == hidden_model or hidden_model.endswith(f".{model_dict.model.__name__}") for hidden_model in HIDDEN_MODELS):
        try:
            admin.site.unregister(model_dict.model)
        except:
            pass 