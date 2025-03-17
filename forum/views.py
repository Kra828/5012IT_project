from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import DiscussionBoard, Post, Comment, Notification, Like
from courses.models import Course
from django.http import JsonResponse

class DiscussionBoardListView(LoginRequiredMixin, ListView):
    """讨论区列表视图"""
    model = DiscussionBoard
    template_name = 'forum/board_list.html'
    context_object_name = 'boards'
    
    def get_queryset(self):
        # 获取所有讨论区
        return DiscussionBoard.objects.all()

class DiscussionBoardDetailView(LoginRequiredMixin, DetailView):
    """讨论区详情视图"""
    model = DiscussionBoard
    template_name = 'forum/board_detail.html'
    context_object_name = 'board'
    pk_url_kwarg = 'board_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取讨论区的所有帖子
        context['posts'] = self.object.posts.all().order_by('-is_pinned', '-created_at')
        # 所有用户都可以发帖
        context['can_post'] = True
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    """创建帖子视图"""
    model = Post
    template_name = 'forum/post_form.html'
    fields = ['title', 'content']
    
    def get_success_url(self):
        return reverse_lazy('forum:board_detail', kwargs={'board_id': self.kwargs['board_id']})
    
    def form_valid(self, form):
        board = get_object_or_404(DiscussionBoard, id=self.kwargs['board_id'])
        form.instance.board = board
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = get_object_or_404(DiscussionBoard, id=self.kwargs['board_id'])
        return context

class PostDetailView(LoginRequiredMixin, DetailView):
    """帖子详情视图"""
    model = Post
    template_name = 'forum/post_detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all().order_by('created_at')
        # 所有用户都可以评论
        context['can_comment'] = True
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # 增加浏览量
        self.object.increment_view()
        return response

class PostUpdateView(LoginRequiredMixin, UpdateView):
    """更新帖子视图"""
    model = Post
    template_name = 'forum/post_form.html'
    fields = ['title', 'content']
    pk_url_kwarg = 'post_id'
    
    def get_success_url(self):
        return reverse_lazy('forum:post_detail', kwargs={
            'board_id': self.kwargs['board_id'],
            'post_id': self.kwargs['post_id']
        })
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = self.object.board
        return context

class PostDeleteView(LoginRequiredMixin, DeleteView):
    """删除帖子视图"""
    model = Post
    template_name = 'forum/post_confirm_delete.html'
    pk_url_kwarg = 'post_id'
    
    def get_success_url(self):
        return reverse_lazy('forum:board_detail', kwargs={'board_id': self.kwargs['board_id']})

class CommentCreateView(LoginRequiredMixin, View):
    """创建评论视图"""
    def post(self, request, board_id, post_id):
        post = get_object_or_404(Post, id=post_id, board_id=board_id)
        content = request.POST.get('content')
        
        if content:
            Comment.objects.create(
                post=post,
                author=request.user,
                content=content
            )
        
        return redirect('forum:post_detail', board_id=board_id, post_id=post_id)

class ReplyCreateView(LoginRequiredMixin, View):
    """创建回复视图"""
    def post(self, request, board_id, post_id, comment_id):
        post = get_object_or_404(Post, id=post_id, board_id=board_id)
        parent_comment = get_object_or_404(Comment, id=comment_id, post=post)
        content = request.POST.get('content')
        
        if content:
            Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
                parent=parent_comment
            )
        
        return redirect('forum:post_detail', board_id=board_id, post_id=post_id)

class CommentUpdateView(LoginRequiredMixin, UpdateView):
    """更新评论视图"""
    model = Comment
    template_name = 'forum/comment_form.html'
    fields = ['content']
    pk_url_kwarg = 'comment_id'
    
    def get_success_url(self):
        return reverse_lazy('forum:post_detail', kwargs={
            'board_id': self.kwargs['board_id'],
            'post_id': self.kwargs['post_id']
        })
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.object.post
        return context

class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """删除评论视图"""
    model = Comment
    template_name = 'forum/comment_confirm_delete.html'
    pk_url_kwarg = 'comment_id'
    
    def get_success_url(self):
        return reverse_lazy('forum:post_detail', kwargs={
            'board_id': self.kwargs['board_id'],
            'post_id': self.kwargs['post_id']
        })

class LikePostView(LoginRequiredMixin, View):
    """点赞帖子视图"""
    def post(self, request, board_id, post_id):
        post = get_object_or_404(Post, id=post_id, board_id=board_id)
        
        # 检查用户是否已经点赞
        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type='post',
            post=post,
            defaults={'comment': None}
        )
        
        if not created:
            # 如果已经点赞，则取消点赞
            like.delete()
        
        return redirect('forum:post_detail', board_id=board_id, post_id=post_id)

class LikeCommentView(LoginRequiredMixin, View):
    """点赞评论视图"""
    def post(self, request, board_id, post_id, comment_id):
        post = get_object_or_404(Post, id=post_id, board_id=board_id)
        comment = get_object_or_404(Comment, id=comment_id, post=post)
        
        # 检查用户是否已经点赞
        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type='comment',
            comment=comment,
            defaults={'post': None}
        )
        
        if not created:
            # 如果已经点赞，则取消点赞
            like.delete()
        
        return redirect('forum:post_detail', board_id=board_id, post_id=post_id)

class NotificationListView(LoginRequiredMixin, ListView):
    """通知列表视图"""
    model = Notification
    template_name = 'forum/notification_list.html'
    context_object_name = 'notifications'
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

class MarkNotificationReadView(LoginRequiredMixin, View):
    """标记通知为已读视图"""
    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.mark_as_read()
        return redirect('forum:notification_list')

class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """标记所有通知为已读视图"""
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return redirect('forum:notification_list')
