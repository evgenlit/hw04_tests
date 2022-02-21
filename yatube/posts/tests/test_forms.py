from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


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

        post_text = 'Тест пост'
        cls.post = Post.objects.create(
            text=post_text,
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        post_text = 'Тестовый пост из формы'
        form_data = {
            'text': post_text,
            'group': PostFormTests.group.id
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': PostFormTests.author.username}))

        self.assertEqual(Post.objects.count(), posts_count + 1)

        last_post = Post.objects.order_by('-id')[:1].get()

        self.assertEqual(
            last_post.text,
            post_text)
        self.assertEqual(
            last_post.group.slug,
            PostFormTests.group.slug)
        self.assertEqual(
            last_post.author.username,
            PostFormTests.author.username)

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        post_text = 'Новое значение для редактируемого поста!'

        form_data = {
            'text': post_text,
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

        editable_post = Post.objects.get(pk=PostFormTests.post.pk)

        self.assertEqual(editable_post.text, post_text)
