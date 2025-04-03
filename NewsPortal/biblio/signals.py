from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from .models import Post, Category
import logging

logger = logging.getLogger(__name__)


@receiver(m2m_changed, sender=Post.categories.through)     # проверка на время
def notify_about_new_post(sender, instance, action, **kwargs):
    if action == "post_add":
        try:
            for category in instance.categories.all():
                # Получаем подписчиков через автоматическую таблицу
                subscribers = category.subscribers.all()

                for user in subscribers:
                    send_post_notification(
                        post=instance,
                        category=category,
                        email=user.email,
                        username=user.username  # Передаем имя
                    )

        except Exception as e:
            print(f"Ошибка при отправке уведомлений: {str(e)}")


def send_post_notification(post, category, email, username):   # проверка на время
    try:
        html_content = render_to_string(
            'email/new_post_notification.html',
            {
                'post': post,
                'category': category,
                'site_url': settings.SITE_URL,
                'username': username,  # Используем в шаблоне
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
        print(f"Ошибка при формировании письма: {str(e)}")




# @receiver(m2m_changed, sender=Post.categories.through)
# def notify_about_new_post(sender, instance, action, pk_set, **kwargs):
#     if action == "post_add" and instance.post_type == 'NW' and pk_set:
#         logger.debug(f"Запуск сигнала для новости: {instance.title}")
#
#         try:
#             categories = Category.objects.filter(id__in=pk_set)
#             if not categories:
#                 return
#
#             subscribers_emails = set()
#
#             for category in categories:
#                 subscribers = category.subscribers.all()
#                 for user in subscribers:
#                     if user.email:
#                         subscribers_emails.add(user.email)
#
#             if subscribers_emails:
#                 send_post_notification(instance, categories.first(), subscribers_emails)
#
#         except Exception as e:
#             logger.error(f"Ошибка при отправке уведомлений: {str(e)}", exc_info=True)



# def send_post_notification(post, category, recipients):
#     """
#     Отправка email-уведомления о новой публикации
#     """
#     try:
#         subject = f'Новая публикация в категории "{category.name}"'
#
#         # Формируем URL для отписки с учетом пространства имен
#         unsubscribe_url = settings.SITE_URL + reverse('biblio:subscribe', args=[category.id])
#
#         html_content = render_to_string(
#             'email/new_post_notification.html',
#             {
#                 'post': post,
#                 'category': category,
#                 'site_url': settings.SITE_URL,
#                 'unsubscribe_url': unsubscribe_url  # Явно передаем URL отписки
#             }
#         )
#
#         if settings.DEBUG:
#             logger.debug(f"Тестовая отправка письма подписчикам: {recipients}")
#             logger.debug(f"Unsubscribe URL: {unsubscribe_url}")
#             logger.debug(html_content)
#             return
#
#         msg = EmailMultiAlternatives(
#             subject=subject,
#             body='',
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             bcc=list(recipients),
#         )
#         msg.attach_alternative(html_content, "text/html")
#         msg.send()
#
#     except Exception as e:
#         logger.error(f"Ошибка при отправке письма: {str(e)}", exc_info=True)