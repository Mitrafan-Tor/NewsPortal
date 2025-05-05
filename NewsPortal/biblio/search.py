from django_filters import FilterSet, DateTimeFilter, ModelMultipleChoiceFilter  # , CharFilter
from .models import Post, Category  # , PostCategory
from django.forms import DateTimeInput

# Создаем свой набор фильтров для модели Product.
# FilterSet, который мы наследуем,
# должен чем-то напомнить знакомые вам Django дженерики.
class SearchPost(FilterSet):
   created_at = DateTimeFilter(
        field_name='created_at',
        lookup_expr='gt',
        widget=DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local'}
        )
   )

   class Meta:
       model = Post
       fields = {
           'title': ['icontains'],
           'author__user__username': ['icontains'],
       }

   category=ModelMultipleChoiceFilter(
           field_name='postcategory__category__name',
           queryset=Category.objects.all(),
           label='Категория',
           conjoined=True,
       )



