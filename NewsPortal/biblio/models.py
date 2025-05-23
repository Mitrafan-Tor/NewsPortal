from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache

from django.utils.translation import gettext as _
from django.utils.translation import pgettext_lazy # импортируем «ленивый» геттекст с подсказкой

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    def update_rating(self):
        # Суммарный рейтинг статей автора * 3
        posts_rating = self.post_set.aggregate(models.Sum('rating'))['rating__sum'] or 0
        posts_rating *= 3

        # Суммарный рейтинг комментариев автора
        author_comments_rating = Comment.objects.filter(user=self.user).aggregate(
            models.Sum('rating'))['rating__sum'] or 0

        # Суммарный рейтинг комментариев к статьям автора
        posts_comments_rating = Comment.objects.filter(post__author=self).aggregate(
            models.Sum('rating'))['rating__sum'] or 0

        # Обновляем рейтинг автора
        self.rating = posts_rating + author_comments_rating + posts_comments_rating
        self.save()

class Category(models.Model):
    name = models.CharField(max_length=255, help_text=_('category name'), unique=True)
    subscribers = models.ManyToManyField(User, blank = True, related_name='categories')

    def __str__(self):
        return self.name


class Post(models.Model):
    NEWS = 'NW'
    ARTICLE = 'AR'
    POST_TYPES = [
        (NEWS, 'Новость'),
        (ARTICLE, 'Статья')
    ]

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=2, choices=POST_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(Category, through='PostCategory')
    title = models.CharField(max_length=255)
    text = models.TextField()
    rating = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title}: {self.text[:20]}"

    def get_absolute_url(self):
        return reverse('biblio:news_detail', args=[str(self.id)])

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def preview(self):
        return f"{self.text[:124]}..."  # Укороченный превью-текст

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Сначала сохраняем объект
        cache.delete(f'post-{self.pk}')  # Затем чистим кэш для этого поста
        # Можно также очистить кэш списков, если нужно:
        cache.delete('latest_news')
        cache.delete('latest_articles')

    @classmethod
    def get_today_news_count(cls, author):
        today = timezone.now().date()
        return cls.objects.filter(
            author=author,
            post_type=cls.NEWS,
            created_at__date=today
        ).count()

    def clean(self):
        if self.post_type == self.NEWS and self.author:
            today_news_count = Post.get_today_news_count(self.author)
            if today_news_count >= 3 and not self.pk:
                raise ValidationError("Нельзя публиковать более 3 новостей в сутки.")
        super().clean()


class PostCategory(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def __str__(self):
        return f"{self.user.username}: {self.text[:20]}"


class School(models.Model):
   name = models.CharField(max_length=64, unique=True)
   address = models.CharField(max_length=120)
   is_active = models.BooleanField(default=True)


class SClass(models.Model):
   grade = models.IntegerField()
   school = models.ForeignKey(School, on_delete=models.CASCADE)


class Student(models.Model):
   name = models.CharField(max_length=64)
   sclass = models.ForeignKey(SClass, on_delete=models.CASCADE)