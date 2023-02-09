import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import PostForm, CommentForm
from ..models import Group, Post, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="author")
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
        cls.group = Group.objects.create(
            title="test-group",
            slug="test-slug",
            description="test-description",
        )
        cls.group_edit = Group.objects.create(
            title="test-group-edit",
            slug="test-slug-edit",
            description="test-description-edit",
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text="Тестовый пост из метода класса",
            image=cls.uploaded
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client_author = Client()
        self.client_author.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст",
            "group": self.group.id,
            "image": self.uploaded
        }
        response = self.client_author.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.get(text=form_data["text"])
        # Комментарий для ревьювера: Post.objects.last() почему-то выбирал из
        # базы пост созданный в методе класса, по этом я воспользовался
        # Post.objects.get
        self.assertRedirects(response, reverse("posts:profile", kwargs={
            "username": self.author.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(new_post.author, self.author)
        self.assertEqual(new_post.group, self.group)

    def test_edit_post(self):
        """Валидная форма релактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            "text": "Измененный тестовый пост из метода класса",
            "group": self.group_edit.id,
        }

        response = self.client_author.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True
        )
        old_group_response = self.client_author.get(
            reverse("posts:group_list", args=(self.group.slug,))
        )
        new_group_response = self.client_author.get(
            reverse("posts:group_list", args=(self.group_edit.slug,)))
        self.assertRedirects(response, reverse("posts:post_detail", kwargs={
            "post_id": self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text="Измененный тестовый пост из метода класса",
            ).exists()
        )
        self.assertEqual(
            old_group_response.context["page_obj"].paginator.count,
            0)
        self.assertEqual(
            new_group_response.context["page_obj"].paginator.count,
            1)


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="author")
        cls.user = User.objects.create_user(username="user")
        cls.post = Post.objects.create(
            author=cls.author,
            text="Тестовый пост из метода класса",
        )
        cls.form = CommentForm()

    def setUp(self):
        self.client_author = Client()
        self.client_author.force_login(self.author)
        self.client_user = Client()
        self.client_user.force_login(self.user)

    def comment_can_create_any_authorised_user(self):
        """Зарегистрированные пользователи могут оставить комментарий
        на странице с постом."""
        comments_count = Comment.objects.select_related("post").all().count()
        form_data = {
            "text": "Тестовый комментарий",
        }
        response = self.client_user.post(
            reverse("posts:add_comment", kwargs={
                "post_id": self.post.pk}),
            data=form_data,
            follow=True
        )
        new_comment = Comment.objects.get(text=form_data["text"])
        self.assertRedirects(response, reverse("posts:post_detail", kwargs={
            "post_id": self.post.pk}))
        self.assertEqual(Comment.objects.select_related("post").all().count(),
                         comments_count + 1)
        self.assertEqual(new_comment.author, self.user)

    def comment_cant_create_unauthorised_user(self):
        """Не зарегистрированные пользователи не могут оставить комментарий
                на странице с постом."""
        comments_count = Comment.objects.select_related("post").all().count()
        form_data = {
            "text": "Тестовый комментарий",
        }
        self.client.post(
            reverse("posts:add_comment", kwargs={
                "post_id": self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.select_related("post").all().count(),
                         comments_count)
