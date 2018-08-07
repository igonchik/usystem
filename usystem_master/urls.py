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
    url(r'^connectvnc/(?P<uid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', connectvnc, name='connectvnc'),
    url(r'^control/', control, name='control'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
