from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from .models import Group, Post, User
from .forms import PostForm

POSTS_ON_PAGE: int = 10


def paginator_object(request, post_list):
    paginator = Paginator(post_list, POSTS_ON_PAGE)
    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    # Получаем набор записей для страницы с запрошенным номером
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    title = 'Последние обновления на сайте'
    post_list = Post.objects.all()
    page_obj = paginator_object(request, post_list)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    title = 'Здесь будет информация о группах проекта Yatube'
    post_list = group.posts.all()
    page_obj = paginator_object(request, post_list)
    context = {
        'group': group,
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author)
    page_obj = paginator_object(request, post_list)
    context = {
        'page_obj': page_obj,
        'author': author,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_number = post.author.posts.count()
    context = {
        'post': post,
        'post_number': post_number
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post = form.save()
        return redirect('posts:post_detail', post_id)
    is_edit = True
    context = {
        'form': form,
        'is_edit': is_edit,
        'post_id': post_id,
    }
    return render(request, 'posts/create_post.html', context)
