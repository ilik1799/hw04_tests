from django.conf import settings
from django.core.cache import cache
from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cache.clear()
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
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__"""
        group = PostModelTest.group
        expected_object_group = group.title
        self.assertEqual(expected_object_group, str(group))
        post = PostModelTest.post
        expected_object_post = post.text
        self.assertEqual(expected_object_post, str(post))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Содержание поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_models_have_correct_object_name_post(self):
        post = PostModelTest.post
        group = PostModelTest.group
        field_string = {
            post.text[:15]: str(post),
            group.title: str(group)
        }
        for expected, value in field_string.items():
            with self.subTest(value=value):
                self.assertEqual(expected, value)
