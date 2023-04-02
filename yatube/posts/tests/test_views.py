import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
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

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
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
            group=cls.group,
            image=SimpleUploadedFile(
                name="small.gif", content=small_gif, content_type="image/gif",
            ),
        )
        cls.POST_EDIT = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.pk})
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.pk})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
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
        response = self.guest_client.get(GROUP)
        expected = list(Post.objects.filter(group=self.group.pk))
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_profile_show_correct_context(self):
        """Проверка контекста posts:profile"""
        response = self.guest_client.get(PROFILE)
        expected = list(Post.objects.filter(author=self.author))
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_post_detail_show_correct_context(self):
        """Проверка контекста posts:post_detail"""
        response = self.authorized_client.get(self.POST_DETAIL)
        post_odj = response.context.get('post')
        self.assertEqual(post_odj, self.post)

    form_fields = {
        'text': forms.fields.CharField,
        'group': forms.fields.ChoiceField,
    }

    def test_edit_post_show_correct_context(self):
        """Проверка контекста редактирование поста posts:post_create"""
        response = self.authorized_client.get(self.POST_EDIT)
        self.assertTrue(response.context.get('is_edit'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                field = response.context.get('form').fields[value]
                self.assertIsInstance(field, expected)

    def test_create_post_show_correct_context(self):
        """Проверка контекста создания поста posts:post_create"""
        response = self.authorized_client.get(CREATE)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                field = response.context.get('form').fields[value]
                self.assertIsInstance(field, expected)

    def test_post_created_not_show_group_profile(self):
        """Проверка отсутстствия постов не в той группе"""
        urls = (
            reverse('posts:group_list', kwargs={
                'slug': self.groupSecond.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertEqual(len(page_obj), 0)

    def test_post_created_show_group_and_profile(self):
        """Проверка постов на странице группы и пользователя"""
        urls = (GROUP, PROFILE)
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
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
        ) for i in range(15))
        Post.objects.bulk_create(posts)

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_paginator_index_page(self):
        """Проверяем выведение постов на index"""
        response = self.guest_client.get(INDEX)
        self.assertEqual(
            len(response.context.get('page_obj')), settings.POSTS_ON_PAGE
        )

    def test_paginator_index_page_two(self):
        """Проверяем выведение оставшихся постов на 2 странице"""
        response = self.guest_client.get(INDEX + '?page=2')
        self.assertEqual(len(response.context.get('page_obj')), 5)
