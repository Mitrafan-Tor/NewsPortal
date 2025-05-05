from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')), # подключаем встроенные эндопинты для работы с локализацией
    path('admin/', admin.site.urls),
    path('pages/', include('django.contrib.flatpages.urls')),
    path('', include('protect.urls')),
    path('sign/', include('sign.urls')),
    path('appointment/', include(('appointment.urls'), namespace='appointment')),
    path('accounts/', include('allauth.urls')),
    path('', include('biblio.urls')),
]




