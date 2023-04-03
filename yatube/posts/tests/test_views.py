from django import forms
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

INDEX = reverse('posts:index')
CREATE = reverse('posts:post_create')
GROUP = reverse('posts:group_list',
                kwargs={'slug': settings.SLUG})
PROFILE = reverse('posts:profile',
                  kwargs={'username': settings.USER_NAME})
USER_NAME = 'TestAuthor'
GROUP_SECOND_TITLE = 'Тестовая группа-2'
SLUG_2 = 'test_slug_2'
DESCRIPTION_2 = 'Тестовое описание-2'
POST_TEXT = 'Тестовый текст'


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username=settings.USER_NAME)
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title=settings.GROUP_TITLE,
            slug=settings.SLUG,
            description=settings.DESCRIPTION
        )
        cls.groupSecond = Group.objects.create(
            title=GROUP_SECOND_TITLE,
            slug=SLUG_2,
            description=DESCRIPTION_2
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=settings.POST_TEXT,
            group=cls.group
        )
        cls.POST_EDIT = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.pk})
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.pk})

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': INDEX,
            'posts/group_list.html': GROUP,
            'posts/profile.html': PROFILE,
            'posts/post_detail.html': self.POST_DETAIL,
            'posts/create_post.html': self.POST_EDIT,
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Проверка контекста posts:index"""
        response = self.authorized_client.get(INDEX)
        first_object = response.context.get('page_obj')[0]
        self.assertEqual(first_object.author.username, self.author.username)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group.title, self.group.title)

    def test_group_list_show_correct_context(self):
        """Проверка контекста posts:group_list"""
        response = self.client.get(GROUP)
        self.assertEqual(list(response.context.get('page_obj')),
                         list(Post.objects.filter(group=self.group.pk))
                         )

    def test_profile_show_correct_context(self):
        """Проверка контекста posts:profile"""
        response = self.client.get(PROFILE)
        expected = list(Post.objects.filter(author=self.author))
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_post_edit_and_post_create_show_correct_context(self):
        """Шаблон post_create и post_edit сформированы с правильной формой
        из контекста."""
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url in urls:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_edit_and_post_create_show_correct_context(self):
        """Шаблон post_create и post_edit сформированы с правильной формой
        из контекста."""
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url in urls:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        post_id = response.context['post_id']
        is_edit = response.context['is_edit']
        self.assertEqual(post_id, self.post.pk)
        self.assertTrue(is_edit)

    def test_post_created_not_show_group_profile(self):
        """Проверка отсутстствия постов не в той группе"""
        urls = (
            reverse('posts:group_list', kwargs={
                'slug': self.groupSecond.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertEqual(len(page_obj), 0)

    def test_post_created_show_group_and_profile(self):
        """Проверка постов на странице группы и пользователя"""
        urls = (GROUP, PROFILE)
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertEqual(len(page_obj), 1)


class PaginatorViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username=settings.USER_NAME)
        cls.group = Group.objects.create(
            title=settings.GROUP_TITLE,
            slug=settings.SLUG,
            description=settings.DESCRIPTION
        )
        posts = (Post(
            text=settings.POST_TEXT,
            group=cls.group,
            author=cls.author,
        ) for _ in range(13))
        Post.objects.bulk_create(posts)

    def test_paginator_index_page(self):
        """Проверяем выведение постов на index"""
        response = self.client.get(INDEX)
        self.assertEqual(
            len(response.context.get('page_obj')), settings.POSTS_ON_PAGE
        )

    def test_paginator_index_page_two(self):
        """Проверяем выведение оставшихся постов на 2 странице"""
        response = self.client.get(INDEX + '?page=2')
        self.assertEqual(len(response.context.get('page_obj')), 3)
