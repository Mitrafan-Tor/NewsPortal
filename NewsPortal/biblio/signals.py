from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.template.loader import render_to_string
from appointment.tasks import send_new_post_notifications
from .models import Post
import logging


logger = logging.getLogger(__name__)

@receiver(m2m_changed, sender=Post.categories.through)
def notify_about_new_post(sender, instance, action, **kwargs):
    if action == "post_add" and instance.post_type == Post.NEWS:
        try:
            # Отправляем задачу в Celery
            send_new_post_notifications.delay(instance.id)
            logger.info(f"Задача на отправку уведомлений для поста {instance.id} поставлена в очередь")
        except Exception as e:
            logger.error(f"Ошибка при постановке задачи в Celery: {str(e)}")


def send_post_notification(post, category, email, username):
    try:
        html_content = render_to_string(
            'email/new_post_notification.html',
            {
                'post': post,
                'category': category,
                'site_url': settings.SITE_URL,
                'username': username,
            }
        )

        msg = EmailMultiAlternatives(
            subject=f'Новая публикация в категории "{category.name}"',
            body='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    except Exception as e:
        logger.error(f"Ошибка при формировании письма: {str(e)}")