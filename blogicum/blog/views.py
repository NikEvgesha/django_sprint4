import datetime

from django.shortcuts import render
from django.shortcuts import get_object_or_404

from .models import Post, Category

POSTS_LIMIT = 5


def index(request):
    template = 'blog/index.html'
    now = datetime.datetime.now()
    posts = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(
        pub_date__lte=now,
        is_published=True,
        category__is_published=True
    ).order_by(
        '-pub_date')[:POSTS_LIMIT]
    context = {
        'post_list': posts
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'blog/detail.html'
    now = datetime.datetime.now()
    queryset = Post.objects.select_related(
        'category',
        'location',
        'author')
    post = get_object_or_404(
        queryset,
        pk=post_id,
        is_published=True,
        category__is_published=True,
        pub_date__lte=now)
    context = {'post': post}
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    now = datetime.datetime.now()
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True)
    category_posts = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(
        category__slug=category_slug,
        is_published=True,
        pub_date__lte=now)
    context = {
        'category': category,
        'post_list': category_posts
    }
    return render(request, template, context)
