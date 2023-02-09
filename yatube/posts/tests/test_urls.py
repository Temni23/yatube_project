from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostUrlsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.author = User.objects.create_user(username="author")
        cls.group = Group.objects.create(
            title="test-group",
            slug="test-slug",
            description="test-description",
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text="test text post" * 10,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.client_author = Client()
        self.client_author.force_login(self.author)

    def test_urls_for_guest_user(self):
        """Проверка корректности работы ссылок
        для неавторизованного пользователя"""
        url_names = ["/", f"/group/{self.group.slug}/",
                     f"/profile/{self.user.username}/",
                     f"/posts/{self.post.id}/"]
        for adress in url_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Страница 404 доступна любому пользователю."""
        response = self.guest_client.get("/random-url/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_post_page(self):
        """Страница создания поста доступна авторизованному пользователю."""
        response = self.authorized_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_page_anonym_user(self):
        """Неавторизованный пользователь со страницы создания поста
         переадресуется на страницу авторизации."""
        response = self.guest_client.get("/create/", follow=True)
        self.assertRedirects(response, ("/auth/login/?next=/create/"))

    def test_edit_post_page(self):
        """Страница редактирования поста доступна автору."""
        response = self.client_author.get(f"/posts/{self.post.id}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_page_not_author(self):
        """Пользователь не являющийся автором
        при попытке радактирования попадает на страницу поста."""
        response = self.authorized_client.get(f"/posts/{self.post.id}/edit/",
                                              follow=True)
        self.assertRedirects(response, (f"/posts/{self.post.id}/"))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            "/": "posts/index.html",
            f"/group/{self.group.slug}/": "posts/group_list.html",
            f"/profile/{self.user.username}/": "posts/profile.html",
            f"/posts/{self.post.id}/": "posts/post_detail.html",
            "/create/": "posts/create_post.html",
            f"/posts/{self.post.id}/edit/": "posts/create_post.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.client_author.get(address)
                self.assertTemplateUsed(response, template)
