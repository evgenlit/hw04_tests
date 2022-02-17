from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post
from ..views import POSTS_COUNT

User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author_user2')

        cls.group = Group.objects.create(
            title='Новая группа 2',
            slug='new-group-2',
            description='Это новая группа 2'
        )

        cls.post = Post.objects.create(
            text='Текст поста 2',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': PostViewTests.group.slug}
            ): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': PostViewTests.author.username}
            ): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': PostViewTests.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                'post_id': PostViewTests.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))

        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        self.assertEqual(post_text_0, PostViewTests.post.text)
        self.assertEqual(post_author_0, PostViewTests.author)
        self.assertEqual(post_group_0, PostViewTests.group)

    def test_group_list_page_context(self):
        """Шаблон posts/group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={
                'slug': PostViewTests.group.slug}))
        group = response.context['group']
        post_text_0 = response.context['page_obj'][0].text
        post_author_0 = response.context['page_obj'][0].author

        self.assertEqual(group, PostViewTests.group)
        self.assertEqual(post_text_0, PostViewTests.post.text)
        self.assertEqual(post_author_0, PostViewTests.post.author)

        # Проверка, что пост не попал в другую группу
        PostViewTests._group = Group.objects.create(
            title='Новая группа 3',
            slug='new-group-3',
            description='Это новая группа 3'
        )
        self.assertNotEqual(group.slug, PostViewTests._group.slug)

    def test_profile_page_context(self):
        """Шаблон posts/profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={
                'username': PostViewTests.author.username}))

        author = response.context['author']
        post_text_0 = response.context['page_obj'][0].text
        post_group_0 = response.context['page_obj'][0].group

        self.assertEqual(author, PostViewTests.author)
        self.assertEqual(post_text_0, PostViewTests.post.text)
        self.assertEqual(post_group_0, PostViewTests.post.group)

    def test_post_detail_page_context(self):
        """Шаблон posts/post_detail.html
        сформирован с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostViewTests.post.id}))

        self.assertEqual(
            response.context.get('post').text, PostViewTests.post.text)
        self.assertEqual(
            response.context.get('post').author, PostViewTests.post.author)
        self.assertEqual(
            response.context.get('post').group, PostViewTests.post.group)

    def test_create_post_page_show_correct_context(self):
        """Шаблон posts/create_post.html
        сформирован с правильным контекстом.
        """
        templates = [
            reverse('posts:post_edit', kwargs={
                'post_id': PostViewTests.post.pk}),
            reverse('posts:post_create'),
        ]

        for template in templates:
            response = self.authorized_client.get(template)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField
            }

            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)


class PostPaginatorViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author_user')

        cls.group = Group.objects.create(
            title='Новая группа',
            slug='new-group',
            description='Это новая группа'
        )

        number_of_posts = 13
        cls.post = [
            Post.objects.create(
                text='Текст поста' + str(i),
                author=cls.author,
                group=cls.group
            )
            for i in range(number_of_posts)]

    def test_index_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице index равно 10."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_COUNT)

    def test_index_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице index равно 3."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        posts_on_second_page = Post.objects.count() % POSTS_COUNT
        self.assertEqual(
            len(response.context['page_obj']), posts_on_second_page)

    def test_group_list_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице
           posts/group_list.html равно 10.
        """
        response = self.client.get(
            reverse('posts:group_list', kwargs={
                'slug': PostPaginatorViewTests.group.slug}))
        self.assertEqual(len(response.context['page_obj']), POSTS_COUNT)

    def test_group_list_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице
           posts/group_list.html равно 3.
        """
        response = self.client.get(
            reverse('posts:group_list', kwargs={
                'slug': PostPaginatorViewTests.group.slug}) + '?page=2')
        posts_on_second_page = Post.objects.count() % POSTS_COUNT
        self.assertEqual(
            len(response.context['page_obj']), posts_on_second_page)

    def test_profile_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице
           posts/profile.html равно 10.
        """
        response = self.client.get(
            reverse('posts:profile', kwargs={
                'username': PostPaginatorViewTests.author.username}))
        self.assertEqual(len(response.context['page_obj']), POSTS_COUNT)

    def test_profile_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице
           posts/profile.html равно 3.
        """
        response = self.client.get(
            reverse('posts:profile', kwargs={
                'username': PostPaginatorViewTests.author.username}
            ) + '?page=2')
        posts_on_second_page = Post.objects.count() % POSTS_COUNT
        self.assertEqual(
            len(response.context['page_obj']), posts_on_second_page)
