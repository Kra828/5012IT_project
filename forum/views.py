from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import DiscussionBoard, Post, Comment, Notification, Like
from courses.models import Course
from django.http import JsonResponse

class DiscussionBoardListView(LoginRequiredMixin, ListView):
    """Discussion board list view"""
    model = DiscussionBoard
    template_name = 'forum/board_list.html'
    context_object_name = 'boards'
    
    def get_queryset(self):
        # Get all discussion boards
        return DiscussionBoard.objects.all()

class DiscussionBoardDetailView(LoginRequiredMixin, DetailView):
    """Discussion board detail view"""
    model = DiscussionBoard
    template_name = 'forum/board_detail.html'
    context_object_name = 'board'
    pk_url_kwarg = 'board_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all posts in the discussion board
        context['posts'] = self.object.posts.all()
        # All users can post
        context['can_post'] = True
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    """Create post view"""
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
    """Post detail view"""
    model = Post
    template_name = 'forum/post_detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # All users can comment
        context['can_comment'] = True
        context['comments'] = self.object.comments.filter(parent__isnull=True)
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Increase view count
        self.object.increment_view()
        return response

class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Update post view"""
    model = Post
    template_name = 'forum/post_form.html'
    fields = ['title', 'content']
    pk_url_kwarg = 'post_id'
    
    def get_success_url(self):
        return reverse_lazy('forum:post_detail', kwargs={
            'board_id': self.object.board.id,
            'post_id': self.object.id
        })
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['board'] = self.object.board
        return context

class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Delete post view"""
    model = Post
    template_name = 'forum/post_confirm_delete.html'
    pk_url_kwarg = 'post_id'
    
    def get_success_url(self):
        return reverse_lazy('forum:board_detail', kwargs={'board_id': self.object.board.id})

class CommentCreateView(LoginRequiredMixin, View):
    """Create comment view"""
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
    """Create reply view"""
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
    """Update comment view"""
    model = Comment
    template_name = 'forum/comment_form.html'
    fields = ['content']
    pk_url_kwarg = 'comment_id'
    
    def get_success_url(self):
        return reverse_lazy('forum:post_detail', kwargs={
            'board_id': self.object.post.board.id,
            'post_id': self.object.post.id
        })
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.object.post
        return context

class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete comment view"""
    model = Comment
    template_name = 'forum/comment_confirm_delete.html'
    pk_url_kwarg = 'comment_id'
    
    def get_success_url(self):
        return reverse_lazy('forum:post_detail', kwargs={
            'board_id': self.object.post.board.id,
            'post_id': self.object.post.id
        })

class LikePostView(LoginRequiredMixin, View):
    """Like post view"""
    def post(self, request, board_id, post_id):
        post = get_object_or_404(Post, id=post_id, board_id=board_id)
        
        # Check if user has already liked
        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type='post',
            post=post,
            defaults={'user': request.user}
        )
        
        # If already liked, unlike
        if not created:
            like.delete()
        
        return redirect('forum:post_detail', board_id=board_id, post_id=post_id)

class LikeCommentView(LoginRequiredMixin, View):
    """Like comment view"""
    def post(self, request, board_id, post_id, comment_id):
        post = get_object_or_404(Post, id=post_id, board_id=board_id)
        comment = get_object_or_404(Comment, id=comment_id, post=post)
        
        # Check if user has already liked
        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type='comment',
            comment=comment,
            defaults={'user': request.user}
        )
        
        # If already liked, unlike
        if not created:
            like.delete()
        
        return redirect('forum:post_detail', board_id=board_id, post_id=post_id)

class NotificationListView(LoginRequiredMixin, ListView):
    """Notification list view"""
    model = Notification
    template_name = 'forum/notification_list.html'
    context_object_name = 'notifications'
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

class MarkNotificationReadView(LoginRequiredMixin, View):
    """Mark notification as read view"""
    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.mark_as_read()
        return redirect('forum:notification_list')

class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Mark all notifications as read view"""
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return redirect('forum:notification_list')
