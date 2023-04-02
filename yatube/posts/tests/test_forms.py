import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User

CREATE = reverse('posts:post_create')
PROFILE = reverse('posts:profile',
                  kwargs={'username': settings.USER_NAME})
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username=settings.USER_NAME
        )
        cls.group = Group.objects.create(
            title=settings.GROUP_TITLE,
            slug=settings.SLUG,
            description=settings.DESCRIPTION
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=settings.POST_TEXT,
            group=cls.group
        )
        cls.POST_EDIT = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.pk})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post_form(self):
        """Проверка формы создание поста автора"""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'text',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            CREATE,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, PROFILE)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            author=self.author,
            image='posts/small.gif',
            text=form_data['text'],
        ).exists(),
            f'Ошибка при создании формы: author={self.author}, '
            f'text={form_data["text"]} '
            f'image={form_data["image"]}',
        )

    def test_edit_post_form(self):
        """Проверка формы редактирования поста"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Test edited_post, please ignore',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            self.POST_EDIT,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(Post.objects.filter(
            text=form_data['text']).exists())
        self.assertTrue(Post.objects.filter(
            group=form_data['group']).exists(),
        )

    def test_auth_create_comment(self):
        """Авторизованный пользователь может комментировать посты"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Test comment, please ignore',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        new_comments_count = Comment.objects.count() - comments_count
        self.assertEqual(new_comments_count,
                         1,
                         'Авторизованный пользователь не может'
                         ' добавлять комментарии',
                         )
        self.assertTrue(Comment.objects.filter(
            text=form_data['text'],
        ).exists(),
            'Не добавился текст комментария из формы',
        )
        self.assertTrue(Comment.objects.filter(
            post=self.post,
        ).exists(),
            'Не добавился комментарий к нужному посту',
        )
        self.assertTrue(Comment.objects.filter(
            author=self.author,
        ).exists(),
            'Комментарий добавляется не от того пользователя',
        )

    def test_guest_create_comment(self):
        '''Гости не могут комментировать посты.'''
        comments_count = Comment.objects.count()
        form_data = {
            "text": "Test guest comment, please ignore",
        }
        self.guest_client.post(
            reverse("posts:add_comment", kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            Comment.objects.count(),
            comments_count,
            'Гость не должен добавлять комментарий',
        )
