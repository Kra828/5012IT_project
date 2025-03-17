from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    # 讨论板
    path('', views.DiscussionBoardListView.as_view(), name='board_list'),
    path('<int:board_id>/', views.DiscussionBoardDetailView.as_view(), name='board_detail'),
    
    # 帖子
    path('<int:board_id>/posts/create/', views.PostCreateView.as_view(), name='post_create'),
    path('<int:board_id>/posts/<int:post_id>/', views.PostDetailView.as_view(), name='post_detail'),
    path('<int:board_id>/posts/<int:post_id>/edit/', views.PostUpdateView.as_view(), name='post_update'),
    path('<int:board_id>/posts/<int:post_id>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    
    # 评论
    path('<int:board_id>/posts/<int:post_id>/comment/', views.CommentCreateView.as_view(), name='comment_create'),
    path('<int:board_id>/posts/<int:post_id>/comment/<int:comment_id>/reply/', 
         views.ReplyCreateView.as_view(), name='reply_create'),
    path('<int:board_id>/posts/<int:post_id>/comment/<int:comment_id>/edit/', 
         views.CommentUpdateView.as_view(), name='comment_update'),
    path('<int:board_id>/posts/<int:post_id>/comment/<int:comment_id>/delete/', 
         views.CommentDeleteView.as_view(), name='comment_delete'),
    
    # 点赞
    path('<int:board_id>/posts/<int:post_id>/like/', views.LikePostView.as_view(), name='like_post'),
    path('<int:board_id>/posts/<int:post_id>/comment/<int:comment_id>/like/', 
         views.LikeCommentView.as_view(), name='like_comment'),
    
    # 通知
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:notification_id>/mark-read/', 
         views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),
] 