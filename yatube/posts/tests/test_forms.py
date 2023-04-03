from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

USER_NAME = 'TestAuthor'
GROUP_TITLE = 'Тестовая группа'
SLUG = 'test_slug'
DESCRIPTION = 'Тестовое описание'
POST_TEXT = 'Тестовый текст'
UPDATED_TEXT = 'Новый текстовый документ'
TEST_TEXT = 'Тестовый текст'

PROFILE = reverse('posts:profile',

                  kwargs={'username': USER_NAME})


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            author='post_author',
        )
        cls.non_author = User.objects.create(
            author='non_post_author',
        )
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=SLUG,
            description=DESCRIPTION
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=POST_TEXT,
            group=cls.group
        )
        cls.POST_EDIT = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.pk})

    def setUp(self):
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
            'group': self.group.id,
            'text': UPDATED_TEXT,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )
        result = Post.objects.get(id=self.post.id)
        self.assertNotEqual(result.text)

    def test_unauth_user_cant_publish_post(self):
        # Проверка на невозможность создания поста для не авторизованного гостя
        posts_count = Post.objects.count()
        form_data = {
            'text': TEST_TEXT,
            'group': self.group.pk,
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        response = self.client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_authorized_user_not_edit_post(self):
        # Проверка на невозможность редактирования поста для не авторизованного
        posts_count = Post.objects.count()
        post = Post.objects.create(
            text='Текст поста для редактирования',
            author=self.post_author,
            group=self.group,
        )
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id,
        }
        response = self.authorized_user_second.post(
            reverse(
                'posts:post_edit',
                args=[post.id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redirect = reverse('posts:post_detail', kwargs={'post_id': post.id})
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        edited_post = Post.objects.get(id=post.id)
        self.assertEqual(post.text, edited_post.text)
        self.assertEqual(post.author, edited_post.author)
        self.assertEqual(post.group, edited_post.group)
        self.assertEqual(post.pub_date, edited_post.pub_date)
