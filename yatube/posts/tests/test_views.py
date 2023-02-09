import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Group, Post, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif",
            content=cls.small_gif,
            content_type="image/gif"
        )
        cls.author = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="test-group",
            slug="test-slug",
            description="test-description",
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=("test text post" * 10),
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client_author = Client()
        self.client_author.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse("posts:group_list",
                    kwargs={"slug": self.group.slug}): "posts/group_list.html",
            reverse("posts:profile", kwargs={
                "username": self.author.username}): "posts/profile.html",
            (reverse("posts:post_detail", kwargs={
                "post_id": self.post.id})): "posts/post_detail.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse("posts:post_edit",
                    kwargs={
                        "post_id": self.post.id}): "posts/create_post.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон домашней страницы сформирован с правильным контекстом."""
        response = self.client_author.get(reverse("posts:index"))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context["page_obj"][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_group_page_show_correct_context(self):
        """Шаблон страницы
        группы страницы сформирован с правильным контекстом."""
        response = self.client_author.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug}))
        first_object = response.context["page_obj"][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон страницы автора сформирован с правильным контекстом."""
        response = self.client_author.get(
            reverse("posts:profile",
                    kwargs={"username": self.author.username}))
        first_object = response.context["page_obj"][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон страницы с постом сформирован с правильным контекстом."""
        response = self.client_author.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}))
        post_object = response.context["post"]
        self.assertEqual(post_object.author, self.post.author)
        self.assertEqual(post_object.text, self.post.text)
        self.assertEqual(post_object.group, self.post.group)
        self.assertEqual(post_object.image, self.post.image)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.client_author.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.client_author.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id}))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="test-group",
            slug="test-slug",
            description="test-description",
        )

        posts = []
        for i in range(15):
            posts.append(Post(
                author=cls.author,
                text=f"test text post number {i}",
                group=cls.group
            ))
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.client_author = Client()
        self.client_author.force_login(self.author)

    def test_paginator_mass_first_page(self):
        """Проверка работы перовой страницы пагинатора
        на ломашней, групповой и странице профиля"""
        pages_first = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
            reverse("posts:profile", kwargs={"username": self.author.username})
        ]
        for names in pages_first:
            with self.subTest(names=names):
                response = self.client_author.get(names)
                self.assertEqual(len(response.context["page_obj"]), 10)

    def test_paginator_mass_second_page(self):
        """Проверка работы второй страницы
         пагинатора на ломашней, групповой и странице профиля"""
        pages_second = [
            reverse("posts:index") + "?page=2",
            reverse("posts:group_list",
                    kwargs={"slug": self.group.slug}) + "?page=2",
            reverse("posts:profile",
                    kwargs={"username": self.author.username}) + "?page=2"
        ]
        for names in pages_second:
            with self.subTest(names=names):
                response = self.client_author.get(names)
                self.assertEqual(len(response.context["page_obj"]), 5)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostRenderTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="test-group",
            slug="test-slug",
            description="test-description",
        )
        cls.group_another = Group.objects.create(
            title="test-group_another",
            slug="test-slug_another",
            description="test-description",
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=("test text post" * 10),
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()

    def test_page_include_post(self):
        """Домашняя страница, страница группы,
        страница автора содержит тестовый пост."""

        pages_list = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
            reverse("posts:profile", kwargs={"username": self.author.username})
        ]

        for names in pages_list:
            with self.subTest(names=names):
                response = self.client.get(names)
                objects = response.context["page_obj"]
                self.assertIn(self.post, objects)

    def test_group_page_not_include_post(self):
        """Cтраница группы, не относящаяся к посту,
            не содержит тестовый пост."""
        response = self.client.get(reverse("posts:group_list", kwargs={
            "slug": self.group_another.slug}))
        objects = response.context["page_obj"]
        self.assertNotIn(self.post, objects)

    def test_home_page_cache(self):
        """Домашняя страница рвботает с кэшем"""
        response = self.client.get(reverse("posts:index"))
        response_before = response.content
        Post.objects.get(pk=1).delete()
        posts = Post.objects.all()
        response = self.client.get(reverse("posts:index"))
        response_after = response.content
        self.assertEqual(response_before, response_after)
        self.assertEqual(len(posts), 0)

    def test_home_page_cache_clear(self):
        """Домашняя страница рвботает после очистки кэша не выдает
        созданный ранее пост"""
        response = self.client.get(reverse("posts:index"))
        response_before = response.content
        cache.clear()
        Post.objects.get(pk=1).delete()
        response = self.client.get(reverse("posts:index"))
        response_after = response.content
        self.assertNotEqual(response_before, response_after)


class FollowsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="author")
        cls.user = User.objects.create_user(username="user")
        cls.unfollow_user = User.objects.create_user(username="unfollow_user")
        cls.post = Post.objects.create(
            author=cls.author,
            text="test text post",
        )

    def setUp(self):
        self.client_authotised = Client()
        self.client_authotised.force_login(self.user)
        self.client_unfollow_user = Client()
        self.client_unfollow_user.force_login(self.unfollow_user)

    def test_authorised_user_can_follow_post_author(self):
        """Авторизованный пользователь может сделать подписку на автора"""
        count_follow = Follow.objects.filter(user=self.user).count()
        self.client_authotised.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post.author.username}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.filter(user=self.user).count(),
                         count_follow + 1)
        self.assertEqual(follow.author_id, self.author.id)
        self.assertEqual(follow.user_id, self.user.id)

    def test_authorised_user_can_unfollow_post_author(self):
        """Авторизованный пользователь может отписатьсяот автора"""
        Follow.objects.create(user=self.user, author=self.author)
        count_follow = Follow.objects.filter(user=self.user).count()
        self.client_authotised.post(
            reverse('posts:profile_unfollow',
                    kwargs={
                        'username': self.post.author.username}))
        self.assertEqual(Follow.objects.filter(user=self.user).count(),
                         count_follow - 1)

    def test_follow_page_include_post_author(self):
        """Новая запись автора появляется у подписчиков и не появляется у
        других пользователей вленте"""
        self.follow = Follow.objects.create(user=self.user, author=self.author)
        response_follow = self.client_authotised.get(
            reverse("posts:follow_index"))
        objects_follow = response_follow.context["page_obj"].object_list
        response_unfollow = self.client_unfollow_user.get(
            reverse("posts:follow_index"))
        objects_unfollow = response_unfollow.context["page_obj"].object_list
        self.assertIn(self.post, objects_follow)
        self.assertNotIn(self.post, objects_unfollow)
