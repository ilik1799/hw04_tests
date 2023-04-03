from . import _config_tests
from django.test import TestCase
from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author = User.objects.create(
            username=_config_tests.USER_NAME
        )
        cls.group = Group.objects.create(
            title=_config_tests.GROUP_TITLE,
            slug=_config_tests.SLUG,
            description=_config_tests.DESCRIPTION
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=_config_tests.POST_TEXT,
        )

    def test_models_have_correct_object_names(self):
        # Проверяем, что у моделей корректно работает __str__
        self.assertEqual(PostModelTest.group.title,
                         str(PostModelTest.group)
                         )
        self.assertEqual(PostModelTest.post.text,
                         str(PostModelTest.post)
                         )

    def test_verbose_name(self):
        # verbose_name в полях совпадает с ожидаемым.
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
        # help_text в полях совпадает с ожидаемым.
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
