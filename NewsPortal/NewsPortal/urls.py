from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework import routers
from biblio import views


router = routers.DefaultRouter()
router.register(r'schools', views.SchoolViewset)
router.register(r'classes', views.SClassViewset)
router.register(r'students', views.StudentViewset)


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')), # подключаем встроенные эндопинты для работы с локализацией
    path('admin/', admin.site.urls),
    path('pages/', include('django.contrib.flatpages.urls')),
    path('protect/', include('protect.urls')),
    path('sign/', include('sign.urls')),
    path('appointment/', include(('appointment.urls'), namespace='appointment')),
    path('accounts/', include('allauth.urls')),
    path('', include('biblio.urls')),
    path('swagger-ui/', TemplateView.as_view(
           template_name='swagger-ui.html',
           extra_context={'schema_url':'openapi-schema'}
       ), name='swagger-ui'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]




