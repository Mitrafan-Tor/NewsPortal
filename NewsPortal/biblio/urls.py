from django.urls import path

from django.views.decorators.cache import cache_page
from .views import (
    NewsList, NewsDetail, PostCreate, PostEdit, PostDelete,
    ArticlesList, ArticlesDetail, ArticlesEdit, ArticlesCreate, ArticlesDelete, CategoryListView, subscribe,# test_email,
    # unsubscribe,
)

app_name = 'biblio'

urlpatterns = [
    # Новости
    path('news/', cache_page(60*1)(NewsList.as_view()), name='news_list'),
    path('news/<int:pk>/', cache_page(60*5)(NewsDetail.as_view()), name='news_detail'),
    path('news/create/', PostCreate.as_view(), name='news_create'),
    path('news/<int:pk>/edit/', PostEdit.as_view(), name='news_edit'),
    path('news/<int:pk>/delete/', PostDelete.as_view(), name='news_delete'),

    # Статьи
    path('articles/', ArticlesList.as_view(), name='articles_list'),
    path('articles/<int:pk>/', ArticlesDetail.as_view(), name='articles_detail'),
    path('articles/<int:pk>/edit/', ArticlesEdit.as_view(), name='articles_edit'),
    path('articles/create/', ArticlesCreate.as_view(), name='articles_create'),
    path('articles/<int:pk>/delete/', ArticlesDelete.as_view(), name='articles_delete'),

    path('categories/<int:pk>', CategoryListView.as_view(), name = 'category_list'),
    path('categories/<int:pk>/subscribe', subscribe, name = 'subscribe'),
    
]