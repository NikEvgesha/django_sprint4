import datetime
from typing import Any

from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (ListView,
                                  CreateView,
                                  UpdateView,
                                  DeleteView,
                                  DetailView,
                                  FormView)
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import Http404
from django.utils import timezone

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm


class PostMixin:
    model = Post
    success_url = reverse_lazy('blog:index')
    template_name = 'blog/create.html'
    form_class = PostForm


class BlogListView(ListView):
    now = timezone.now()
    model = Post
    ordering = ['-pub_date']
    paginate_by = 10
    template_name = 'blog/index.html'
    queryset = Post.objects.select_related(
        'author',
        'location',
        'category'
    ).filter(
        pub_date__lte=now,
        is_published=True,
        category__is_published=True
    ).annotate(comment_count=Count('comments'))


class BlogCreateView(LoginRequiredMixin, PostMixin, CreateView):

    def form_valid(self, form):
        form.instance.author = self.request.user
        if form.instance.pub_date is None:
            form.instance.pub_date = datetime.datetime.now()
        post = form.save(commit=False)
        post.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user})


class BlogUpdateView(PostMixin, LoginRequiredMixin, UpdateView):

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', pk=instance.pk)
        return super().dispatch(request, *args, **kwargs)


class BlogDeleteView(PostMixin, LoginRequiredMixin, DeleteView, FormView):
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        if instance.author != request.user:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super(BlogDeleteView, self).get_form_kwargs()
        kwargs['instance'] = get_object_or_404(Post, pk=self.kwargs['pk'])
        return kwargs


class BlogDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        now = timezone.now()
        get_object_or_404(Post,
                          Q(pk=kwargs['pk'])
                          & (Q(author__username=self.request.user.username)
                             | (Q(is_published=True)
                             & Q(category__is_published=True)
                             & Q(pub_date__lte=now))))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.all()
        )
        return context


class UserDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, username=self.kwargs['username'])
        context['profile'] = user
        queryset = Post.objects.select_related(
            'author',
            'location',
            'category'
        ).filter(
            Q(author=user)
            & (Q(is_published=True)
               | Q(author__username=self.request.user.username))
        ).order_by(
            '-pub_date'
        ).annotate(comment_count=Count('comments'))
        paginator = Paginator(queryset, 10)
        page = self.request.GET.get('page')
        posts = paginator.get_page(page)
        context['page_obj'] = posts
        return context

    def get_object(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return user


class UserUpdateView(UpdateView):
    template_name = 'blog/user.html'
    model = User
    fields = ['username', 'first_name', 'last_name', 'email']
    success_url = reverse_lazy('blog:index')

    def get_object(self):
        user = get_object_or_404(User, username=self.request.user)
        return user


class CommentCreateView(LoginRequiredMixin, CreateView):
    cur_post = None
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.cur_post = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.cur_post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['pk']})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['pk']})

    def get_object(self):
        comment = get_object_or_404(Comment, pk=self.kwargs.get('comment_pk'))
        return comment

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_pk'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_pk'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'pk': self.kwargs['pk']})

    def get_object(self):
        comment = get_object_or_404(Comment, pk=self.kwargs.get('comment_pk'))
        return comment


class CategoryListView(ListView):
    model = Post
    ordering = ['-pub_date']
    paginate_by = 10
    template_name = 'blog/category.html'

    def dispatch(self, request, *args, **kwargs):
        get_object_or_404(Category,
                          Q(slug=kwargs['category_slug'])
                          & (Q(is_published=True)))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        now = timezone.now()
        queryset = super().get_queryset()
        return queryset.select_related(
            'author',
            'location',
            'category'
        ).filter(
            category__slug=self.kwargs['category_slug'],
            is_published=True,
            pub_date__lte=now
        ).annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(Category,
                                     slug=self.kwargs.get('category_slug'))
        context['category'] = category
        return context
