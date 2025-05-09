from django.utils import timezone
from datetime import timedelta

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from biblio.models import Post, Category
import logging

@shared_task
def send_weekly_newsletters():
    """
    Еженедельная рассылка новостей подписчикам
    Выполняется каждый понедельник в 8 утра
    """
    try:
        # Получаем все категории с подписчиками
        categories = Category.objects.filter(subscribers__isnull=False).distinct()

        for category in categories:
            # Получаем новости за последнюю неделю в этой категории
            one_week_ago = timezone.now() - timedelta(weeks=1)
            posts = Post.objects.filter(
                categories=category,
                created_at__gte=one_week_ago,
                post_type='NW'  # Только новости
            ).order_by('-created_at')

            if not posts.exists():
                continue

            # Получаем всех подписчиков категории
            subscribers = category.subscribers.all()

            for user in subscribers:
                if not user.email:
                    continue

                try:
                    # Формируем и отправляем письмо
                    send_weekly_newsletter_email(user, category, posts)
                except Exception as e:
                    # Логируем ошибки отправки конкретному пользователю
                    print(f"Ошибка отправки письма пользователю {user.username}: {str(e)}")
                    continue

    except Exception as e:
        # Логируем общие ошибки задачи
        print(f"Ошибка в задаче send_weekly_newsletters: {str(e)}")
        raise  # Переподнимаем исключение для Celery

def send_weekly_newsletter_email(user, category, posts):
    """
    Вспомогательная функция для отправки письма с подборкой новостей
    """
    html_content = render_to_string(
        'email/weekly_newsletter.html',
        {
            'category': category,
            'posts': posts,
            'user': user,
            'site_url': settings.SITE_URL,
        }
    )

    msg = EmailMultiAlternatives(
        subject=f'Еженедельная подборка новостей в категории "{category.name}"',
        body='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()


logger = logging.getLogger(__name__)

@shared_task
def send_new_post_notifications(post_id):
    """
    Отправляет уведомления подписчикам о новой новости
    """
    try:
        post = Post.objects.get(id=post_id)
        if post.post_type != Post.NEWS:
            return  # Отправляем только для новостей

        categories = post.categories.all()
        for category in categories:
            subscribers = category.subscribers.all()
            for user in subscribers:
                if not user.email:
                    continue

                try:
                    send_post_notification_email(user, post, category)
                except Exception as e:
                    logger.error(f"Ошибка отправки письма пользователю {user.username}: {str(e)}")
                    continue

    except Post.DoesNotExist:
        logger.error(f"Пост с id {post_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка в задаче send_new_post_notifications: {str(e)}")
        raise

def send_post_notification_email(user, post, category):
    """
    Вспомогательная функция для отправки email уведомления
    """
    html_content = render_to_string(
        'email/new_post_notification.html',
        {
            'post': post,
            'category': category,
            'site_url': settings.SITE_URL,
            'username': user.username,
        }
    )

    msg = EmailMultiAlternatives(
        subject=f'Новая публикация в категории "{category.name}"',
        body='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()