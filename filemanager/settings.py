import os

from django.conf import settings

FILEMANAGER_STATIC_ROOT = getattr(
    settings,
    'FILEMANAGER_STATIC_ROOT',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'filemanager'),
)
FILEMANAGER_CKEDITOR_JS = getattr(
    settings,
    'FILEMANAGER_CKEDITOR_JS',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ckeditor', 'ckeditor.js'),
)
FILEMANAGER_CHECK_SPACE = getattr(
    settings,
    'FILEMANAGER_CHECK_SPACE',
    True,
)
FILEMANAGER_SHOW_SPACE = getattr(
    settings,
    'FILEMANAGER_SHOW_SPACE',
    FILEMANAGER_CHECK_SPACE,
)
