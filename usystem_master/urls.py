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
                  url(r'^connectvnc/(?P<uid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', connectvnc,
                      name='connectvnc'),
                  url(r'^control_json/$', minion_json, name='minion_json'),
                  url(r'^genadminpin/$', genadminpin, name='genadminpin'),
                  url(r'^add_group/$', add_group, name='add_group'),
                  url(r'^delete_group/(?P<num>\d+)/$', delete_group, name='delete_group'),
                  url(r'^about/(?P<num>\d+)/$', about, name='about'),
                  url(r'^add_group/(?P<num>\d+)/', add_group, name='add_group'),
                  url(r'^updatecert/(?P<num>\d+)/', updatecert, name='updatecert'),
                  url(r'^removeagent/(?P<num>\d+)/', removeagent, name='removeagent'),
                  url(r'^removereq/(?P<num>\d+)/', removereq, name='removereq'),
                  url(r'^connectvnc/(?P<uid>\d+)/$', connectvnc, name='connectvnc'),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
