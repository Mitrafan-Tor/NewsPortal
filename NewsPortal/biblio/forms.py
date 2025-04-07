from django import forms
from .models import Post, Comment, Author

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'post_type', 'categories', 'author']

    def clean(self):
        cleaned_data = super().clean()
        post_type = cleaned_data.get('post_type')
        author = cleaned_data.get('author')

        if post_type == Post.NEWS and author:
            today_news_count = Post.get_today_news_count(author)
            if today_news_count >= 3:
                raise forms.ValidationError("Вы не можете публиковать более 3 новостей в сутки.")
        return cleaned_data




class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')