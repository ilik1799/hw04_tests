from . import _config_tests
from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User
PROFILE = reverse('posts:profile',
                  kwargs={'username': _config_tests.USER_NAME})


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username=_config_tests.USER_NAME
        )
        cls.ne_author = User.objects.create(
            username=_config_tests.RANDOM_USER
        )
        cls.group = Group.objects.create(
            title=_config_tests.GROUP_TITLE,
            slug=_config_tests.SLUG,
            description=_config_tests.DESCRIPTION
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=_config_tests.POST_TEXT,
            group=cls.group
        )
        cls.POST_EDIT = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.pk})

    def setUp(self):
        self.guest_client = Client()
        self.guest_client.force_login(self.ne_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post_form(self):
        # Проверка формы создание поста автора
        post_count = Post.objects.count()
        form_data = {
            'text': 'text',
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, PROFILE)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            author=self.author,
            group=self.group,
            text=form_data['text']).exists()
        )

    def test_edit_post_form(self):
        # Проверка формы редактирования поста
        form_data = {
            'text': 'Новый тестовый текст',
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        result = Post.objects.get(id=self.post.id)
        self.assertNotEqual(result.text, _config_tests.POST_TEXT)

    def test_unauth_user_cant_publish_post(self):
        # Проверка на невозможность создания поста для не авторизованного гостя
        posts_count = Post.objects.count()
        form_data = {
            'text': _config_tests.POST_TEXT,
            'group': self.group.pk,
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit_author_ne_author(self):
        # Проверка на невозможность изменения поста
        form_data_test = {
            'text': _config_tests.CHANGE_POST_TEXT,
            'group': self.group.pk
        }

        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data_test,
            follow=True
        )

        edit_post = Post.objects.get(pk=self.post.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(edit_post.author, self.post.author)
        self.assertNotEqual(edit_post.text, form_data_test['text'])
        self.assertEqual(edit_post.group.pk, self.group.pk)
