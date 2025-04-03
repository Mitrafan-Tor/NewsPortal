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

   # material=ModelMultipleChoiceFilter(
   #         field_name='productmaterial__material',
   #         queryset=Material.objects.all(),
   #         label='Material',
   #         conjoined=True,
   #     )

   #category = CharFilter(field_name='postcategory__category__name', lookup_expr='icontains')

   class Meta:
       model = Post
       fields = {
           'title': ['icontains'],
           'author__user__username': ['icontains'],
           #'postcategory__category__name': ['icontains'],  # Альтернативный вариант
       }

   categpry=ModelMultipleChoiceFilter(
           field_name='postcategory__category__name',
           queryset=Category.objects.all(),
           label='Категория',
           conjoined=True,
       )



