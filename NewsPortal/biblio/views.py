from django.views.generic import ListView, DetailView
from .models import Post
from datetime import datetime
from .search import SearchPost

class NewsList(ListView):
    model = Post
    template_name = 'news/news_list.html'
    context_object_name = 'news'
    queryset = Post.objects.order_by('-created_at')
    paginate_by = 10

    # Переопределяем функцию получения списка товаров
    def get_queryset(self):
        # Получаем обычный запрос
        queryset = super().get_queryset()
        # Используем наш класс фильтрации.
        # self.request.GET содержит объект QueryDict, который мы рассматривали
        # в этом юните ранее.
        # Сохраняем нашу фильтрацию в объекте класса,
        # чтобы потом добавить в контекст и использовать в шаблоне.
        self.filterset = SearchPost(self.request.GET, queryset)
        # Возвращаем из функции отфильтрованный список товаров
        return self.filterset.qs

    # Метод get_context_data позволяет нам изменить набор данных,
    # который будет передан в шаблон.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        # Добавляем подсчет новостей и статей
        context['news_count'] = Post.objects.filter(post_type='NW').count()
        context['article_count'] = Post.objects.filter(post_type='AR').count()
        context['time_now'] = datetime.utcnow()
        context['next_sale'] = "Распродажа в среду!"
        return context

class NewsDetail(DetailView):
    model = Post
    template_name = 'news/news_detail.html'
    context_object_name = 'news'