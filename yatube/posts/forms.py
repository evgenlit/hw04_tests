from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group",)

        labels = {
            "text": "Текст",
            "group": "Группа",
        }

        help_texts = {
            'text': 'Напишите сюда текст поста',
            'group': 'Выберите группу для поста',
        }
