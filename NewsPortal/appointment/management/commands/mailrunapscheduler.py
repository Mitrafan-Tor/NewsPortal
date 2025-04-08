# NewsPortal/appointment/management/commands/mailrunascheduler.py
import logging
from django.conf import settings
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from datetime import timedelta
from biblio.models import Category, Post
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_weekly_newsletter():
    # Получаем все категории с подписчиками
    categories = Category.objects.filter(subscribers__isnull=False).distinct()

    for category in categories:
        # Получаем новости за последнюю неделю в этой категории
        one_week_ago = one_week_ago = timezone.now() - timedelta(weeks=1)
        posts = Post.objects.filter(
            categories=category,
            created_at__gte=one_week_ago,
            post_type='NW'  # Только новости, не статьи
        ).order_by('-created_at')

        if not posts.exists():
            continue

        # Получаем всех подписчиков этой категории
        subscribers = category.subscribers.all()

        for user in subscribers:
            if not user.email:
                continue

            # Формируем содержимое письма
            html_content = render_to_string(
                'email/weekly_newsletter.html',
                {
                    'category': category,
                    'posts': posts,
                    'user': user,
                    'site_url': settings.SITE_URL,
                }
            )

            # Отправляем письмо
            msg = EmailMultiAlternatives(
                subject=f'Еженедельная подборка новостей в категории "{category.name}"',
                body='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()


def delete_old_job_executions(max_age=604_800):
    """Удаляет все записи выполненных задач старше max_age секунд (7 дней)"""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Запускает планировщик задач APScheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Добавляем задачу еженедельной рассылки (каждый понедельник в 8:00)
        scheduler.add_job(
            send_weekly_newsletter,
            trigger=CronTrigger(
                day_of_week="mon", hour="8", minute="00"
            ),
            id="weekly_newsletter",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Добавлена еженедельная задача: 'weekly_newsletter'.")

        # Задача для очистки старых записей
        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Добавлена еженедельная задача: 'delete_old_job_executions'.")

        try:
            logger.info("Запуск планировщика...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Остановка планировщика...")
            scheduler.shutdown()
            logger.info("Планировщик успешно остановлен!")