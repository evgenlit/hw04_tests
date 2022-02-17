from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')

        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Новая тестовая группа'
        )

        cls.post = Post.objects.create(
            text='Тест пост',
            author=cls.author,
            group=cls.group
        )

        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый пост из формы',
            'author': PostFormTests.author.id,
            'group': PostFormTests.group.id
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': PostFormTests.author.username}))

        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост из формы',
                author=PostFormTests.author,
                group=PostFormTests.group
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        # Подсчитаем количество записей в Post
        # и убедимся, что пост был изменён, а не добавлен новый
        posts_count = Post.objects.count()
        new_text_for_post = 'Новое значение для редактируемого поста!'

        form_data = {
            'text': new_text_for_post,
            # 'author': PostFormTests.author.id,
            'group': PostFormTests.group.pk
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostFormTests.post.pk}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': PostFormTests.post.pk}))

        self.assertEqual(Post.objects.count(), posts_count)

        self.assertTrue(
            Post.objects.filter(
                text=new_text_for_post,
                author=PostFormTests.author,
                group=PostFormTests.group
            ).exists()
        )
