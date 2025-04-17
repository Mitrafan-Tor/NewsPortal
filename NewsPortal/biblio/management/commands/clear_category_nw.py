from django.core.management.base import BaseCommand, CommandError
from biblio.models import Post, Category


class Command(BaseCommand):
    help = 'Удаляет все новости из указанной категории'
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument('category', type=str, help='Название категории для очистки новостей')

    def handle(self, *args, **options):
        category_name = options['category']

        try:
            category = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Категория "{category_name}" не найдена'))
            return

        # Получаем количество новостей в категории
        news_count = Post.objects.filter(
            categories=category,
            post_type=Post.NEWS
        ).count()

        if news_count == 0:
            self.stdout.write(self.style.WARNING(f'В категории "{category_name}" нет новостей'))
            return

        self.stdout.write(self.style.WARNING(
            f'Вы собираетесь удалить {news_count} новостей из категории "{category_name}".'
        ))
        self.stdout.write('Это действие нельзя отменить!')

        # Запрос подтверждения
        self.stdout.write('Для подтверждения введите "yes":')
        answer = input().lower()

        if answer == 'yes':
            # Удаляем новости из категории (но не саму категорию)
            posts_to_delete = Post.objects.filter(
                categories=category,
                post_type=Post.NEWS
            )
            deleted_count, _ = posts_to_delete.delete()

            self.stdout.write(self.style.SUCCESS(
                f'Успешно удалено {deleted_count} новостей из категории "{category_name}"'
            ))
        else:
            self.stdout.write(self.style.ERROR('Удаление отменено'))