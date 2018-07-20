# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from usystem.views import *

handler403 = 'usystem_master.errhandlers.error403'
handler404 = 'usystem_master.errhandlers.error403'
handler500 = 'usystem_master.errhandlers.error500'

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', index, name='index'),
    url(r'^/connectvnc/', connectvnc, name='connectvnc'),
    url(r'^/update/$', update_saw, name='update_saw'),
    url(r'^/material/$', material, name='material'),
    url(r'^/material/(?P<num>\d+)/$', material, name='material'),
    url(r'^/zakaz/$', zakaz, name='zakaz'),
    url(r'^/zakaz/(?P<num>\d+)/$', zakaz, name='zakaz'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
