from .models import Author, Category, Post, PostCategory, Comment, MyModel
from django.contrib import admin

from modeltranslation.admin import TranslationAdmin # импортируем модель амдинки (вспоминаем модуль про переопределение стандартных админ-инструментов)


# напишем уже знакомую нам функцию обнуления товара на складе
def nullfy_rating(modeladmin, request, queryset):
    queryset.update(rating=0)

nullfy_rating.short_description = 'Обнулить рейтинг' # описание для более понятного представления в админ панеле задаётся, как будто это объект

# Настраиваем отображение связанных категорий для постов
class PostCategoryInline(admin.TabularInline):
    model = PostCategory
    extra = 1

# Настраиваем отображение постов в админке
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'post_type', 'created_at', 'rating')  # Отображаемые поля в списке
    list_filter = ('post_type', 'categories', 'created_at')  # Фильтры справа
    search_fields = ('title', 'text')  # Поиск по этим полям
    actions = [nullfy_rating]
    inlines = [PostCategoryInline]  # Включаем связанные категории

    def get_readonly_fields(self, request, obj=None):
        if obj:  # При редактировании существующего поста
            return ('author',) + self.readonly_fields
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # Только при создании
            obj.author = request.user.author
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Скрываем поле автора при создании, так как оно устанавливается автоматически
        if not obj:
            if 'author' in form.base_fields:
                del form.base_fields['author']
        return form

# Настраиваем отображение комментариев
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at', 'rating')
    list_filter = ('created_at', 'rating')
    search_fields = ('text', 'user__username')
    actions = [nullfy_rating]

# Настраиваем отображение авторов
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'count_posts')
    search_fields = ('user__username',)
    actions = [nullfy_rating]

    def count_posts(self, obj):
        return obj.post_set.count()
    count_posts.short_description = 'Количество постов'

# Register your models here.

# Регистрируем модели для перевода в админке

class CategoryAdmin(TranslationAdmin):
    model = Category


class MyModelAdmin(TranslationAdmin):
    model = MyModel


admin.site.register(MyModel)
# Регистрируем модели в административной панели
admin.site.register(Author, AuthorAdmin)
admin.site.register(Category)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)

