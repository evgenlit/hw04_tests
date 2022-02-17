from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author_user')

        cls.group = Group.objects.create(
            title='Новая группа 1',
            slug='new-group-1',
            description='Это новая группа 1'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст поста 1',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем обычного пользователя
        self.user = User.objects.create_user(username='auth_user')
        # Создаем клиент авторизованного пользователя
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        # Создаем клиент авторизованного пользователя автора
        self.authorized_client_author = Client()
        # Авторизуем автора
        self.authorized_client_author.force_login(self.author)

    def test_public_url_names_correct_response_code(self):
        """Проверяем доступность URL-адресов для любого пользователя."""
        url_names_response_code = {
            '/': 200,
            '/group/new-group-1/': 200,
            '/profile/author_user/': 200,
            f'/posts/{self.post.id}/': 200,
            '/unexisting_page/': 404
        }
        for address, code in url_names_response_code.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_posts_edit_url_exists_for_author(self):
        """Страница /posts/<post_id>/edit/ доступна автору поста."""
        response_auth_author = self.authorized_client_author.get(
            f'/posts/{self.post.id}/edit/')
        self.assertEqual(response_auth_author.status_code, 200)

        response_auth_user = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(response_auth_user, f'/posts/{self.post.id}/')

    def test_create_page_url_exists_for_auth_user(self):
        """Страница /create/ доступна авторизованным пользователям."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_public_urls_uses_correct_template(self):
        """Общедоступный URL-адрес использует соответствующий шаблон."""
        public_url_names = {
            '/': 'posts/index.html',
            '/group/new-group-1/': 'posts/group_list.html',
            '/profile/author_user/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for address, template in public_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_private_urls_uses_correct_template(self):
        """Приватный URL-адрес использует соответствующий шаблон."""
        private_url_names = {
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in private_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)
