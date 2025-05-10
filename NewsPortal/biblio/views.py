import pytz
from django.contrib.auth.decorators import login_required
from django.core.checks import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect

from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from django.conf import settings
from .models import Post, Category, Author
from .search import SearchPost
from .forms import PostForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, reverse, redirect, get_object_or_404
from django.views import View
from django.core.mail import send_mail
from datetime import datetime
from django.utils import timezone

from appointment.models import Appointment
from .signals import logger
from django.template.loader import render_to_string

from django.core.cache import cache
from django.contrib import messages
from django.utils.translation import gettext as _ # импортируем функцию для перевода

#from .models import MyModel


class PostDetailView(DetailView):
    model = Post
    # template_name определяется в get_template_names()
    def get_object(self, *args, **kwargs):
        cache_key = f'post-{self.kwargs["pk"]}'  # Исправленный ключ кэша
        obj = cache.get(cache_key)

        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(cache_key, obj, timeout=60 * 15)  # Кэшируем на 15 минут
            print(f"Объект закэширован с ключом {cache_key}")  # Для отладки

        return obj

    def get_template_names(self):
        obj = self.get_object()
        if obj.post_type == Post.NEWS:
            return ['news/news_detail.html']
        return ['articles/articles_detail.html']


#Новости
class NewsList(PermissionRequiredMixin, ListView):
    model = Post
    template_name = 'news/news_list.html'
    context_object_name = 'news'
    queryset = Post.objects.filter(post_type='NW').order_by('-created_at')
    paginate_by = 10
    permission_required = ('biblio.view_post',)

    # Переопределяем функцию получения списка товаров
    def get_queryset(self):
        # Получаем обычный запрос
        queryset = super().get_queryset().filter(post_type='NW')
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
        context['time_now'] = datetime.now()
        context['next_sale'] = "Распродажа в среду!"
        return context

class NewsDetail(PermissionRequiredMixin, DetailView):
    model = Post
    template_name = 'news/news_detail.html'
    context_object_name = 'news'
    permission_required = ('biblio.view_post',)


# NewsPortal/biblio/views.py

class PostCreate(PermissionRequiredMixin, CreateView):
    form_class = PostForm
    model = Post
    template_name = 'news/news_create.html'
    permission_required = ('biblio.add_post',)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        try:
            author = Author.objects.get(user=self.request.user)
            form.instance.author = author

            # Проверка лимита новостей
            if form.cleaned_data.get('post_type') == Post.NEWS:
                today = timezone.now().date()
                if Post.objects.filter(
                        author=author,
                        post_type=Post.NEWS,
                        created_at__date=today
                ).count() >= 3:
                    form.add_error(None, "Лимит новостей (3 в день) исчерпан")
                    return self.form_invalid(form)

            return super().form_valid(form)
        except Author.DoesNotExist:
            form.add_error(None, "У вас нет прав автора")
            return self.form_invalid(form)


class PostEdit(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'news/news_edit.html'
    permission_required = ('biblio.change_post',)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Дополнительная защита - проверяем, что пользователь редактирует свой пост
        if form.instance.author.user != self.request.user:
            raise PermissionDenied("Вы можете редактировать только свои публикации")
        return form

    def form_valid(self, form):
        # Дополнительная проверка перед сохранением
        if form.instance.author.user != self.request.user:
            form.add_error(None, "Нельзя изменить автора публикации")
            return self.form_invalid(form)
        return super().form_valid(form)


class PostList(PermissionRequiredMixin, ListView):
    model = Post
    template_name = 'news/news_list.html'
    context_object_name = 'news'
    paginate_by = 10
    permission_required = ('biblio.view_post',)

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
        context['time_now'] = datetime.now()
        context['next_sale'] = "Распродажа в среду!"
        return context


class PostDelete(PermissionRequiredMixin, DeleteView):
    model = Post
    template_name = 'news/news_delete.html'
    success_url = reverse_lazy('news_list'),
    permission_required = ('biblio.delete_post',)


#СТАТЬИ
class ArticlesList(PermissionRequiredMixin, ListView):
    model = Post
    template_name = 'articles/articles_list.html'
    context_object_name = 'article'
    queryset = Post.objects.filter(post_type='AR').order_by('-created_at')
    paginate_by = 10
    permission_required = ('biblio.view_post',)

    # Переопределяем функцию получения списка товаров
    def get_queryset(self):
        # Получаем обычный запрос
        queryset = super().get_queryset().filter(post_type='AR')
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
        context['time_now'] = datetime.now()
        context['next_sale'] = "Распродажа в среду!"
        return context

class ArticlesDetail(PermissionRequiredMixin, DetailView):
     model = Post
     template_name = 'articles/articles_detail.html'
     context_object_name = 'article'
     permission_required = ('biblio.view_post',)


# # Добавляем новое представление для создания товаров.
class ArticlesCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    form_class = PostForm
    model = Post
    template_name = 'articles/articles_create.html'
    permission_required = ('biblio.add_post',)

    def get_success_url(self):
        return reverse('biblio:articles_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        if not hasattr(self.request.user, 'author'):
            messages.error(self.request, "Вы должны стать автором, прежде чем создавать статьи")
            return self.form_invalid(form)

        form.instance.author = self.request.user.author
        return super().form_valid(form)

 # Добавляем представление для изменения товара.
class ArticlesEdit(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    # Указываем нашу разработанную форму
    form_class = PostForm
    # модель товаров
    model = Post
    # и новый шаблон, в котором используется форма.
    template_name = 'articles/articles_edit.html'
    permission_required = ('biblio.change_post',)

# Представление удаляющее товар.
class ArticlesDelete(PermissionRequiredMixin, DeleteView):
    model = Post
    template_name = 'articles/articles_delete.html'
    success_url = reverse_lazy('articles_list')
    permission_required = ('biblio.delete_post',)


class AppointmentView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'make_appointment.html', {})

    def post(self, request, *args, **kwargs):
        appointment = Appointment(
            date=datetime.strptime(request.POST['date'], '%Y-%m-%d'),
            client_name=request.POST['client_name'],
            message=request.POST['message'],
        )
        appointment.save()

        return redirect('appointment:make_appointment')


class CategoryListView(NewsList):
    model = Post
    template_name = "news/category_list.html"
    context_object_name = 'category_news_list'

    def get_queryset(self):
        self.category = get_object_or_404(Category, id.self.kwargs['pk'])
        queryset = Post.objects.filter(category = self.category).order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_ot_subscriber'] = self.request.user_not_in_self.categpry.subscribers.all()
        context['category'] = self.category
        return context


@login_required
def subscribe(request, pk):
    category = get_object_or_404(Category, id=pk)
    user = request.user
    next_url = request.POST.get('next', reverse('biblio:news_list'))

    if user in category.subscribers.all():
        category.subscribers.remove(user)
        # Отправка письма об отписке
        send_subscription_email(user, category, is_subscribed=False)
        return render(request, 'news/unsubscribe.html', {
            'category': category.name,
            'next_url': next_url
        })
    else:
        category.subscribers.add(user)
        # Отправка письма о подписке
        send_subscription_email(user, category, is_subscribed=True)
        return render(request, 'news/subscribe.html', {
            'category': category.name,
            'next_url': next_url
        })


def send_subscription_email(user, category, is_subscribed):
    subject = 'Вы подписались' if is_subscribed else 'Вы отписались'
    template = 'news/subscribe.html' if is_subscribed else 'news/unsubscribe.html'

    try:
        html_message = render_to_string(template, {
            'user': user,
            'category': category,
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
        })

        # Всегда отправляем письмо, независимо от DEBUG
        send_mail(
            subject=subject,
            message='',  # Текстовое сообщение (пустое, так как используем html_message)
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )

    except Exception as e:
        logger.error(f"Ошибка отправки письма: {str(e)}")
        if getattr(settings, 'DEBUG', False):
            print(f"Ошибка отправки: {str(e)}")


# Create your views here.
class Index(View):
    def get(self, request):
        curent_time = timezone.now()
        # . Translators: This message appears on the home page only
        models = Post.objects.all()

        context = {
            'models': models,
            'current_time': timezone.now(),
            'timezones': pytz.common_timezones  # добавляем в контекст все доступные часовые пояса
        }

        return HttpResponse(render(request, 'index.html', context))

        #  по пост-запросу будем добавлять в сессию часовой пояс, который и будет обрабатываться написанным нами ранее middleware

    def post(self, request):
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('/')

@require_POST
def set_timezone(request):
    request.session['django_timezone'] = request.POST['timezone']
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))