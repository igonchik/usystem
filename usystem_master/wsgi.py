import os
from django.core.handlers.wsgi import WSGIHandler
import django


class WSGIEnvironment(WSGIHandler):
    def __call__(self, environ, start_response):
        try:
            os.environ['AUTH_USER'] = environ['SSL_CLIENT_I_DN_CN']
        except:
            os.environ['AUTH_USER'] = ''
        from django.conf import settings
        settings.DATABASES['default']['USER'] = os.environ['AUTH_USER']
        return super(WSGIEnvironment, self).__call__(environ, start_response)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "usystem_master.settings")
django.setup(set_prefix=False)
application = WSGIEnvironment()

