from django.conf import settings

FILEMANAGER_STATIC_ROOT = getattr(settings, 'FILEMANAGER_STATIC_ROOT',
                            'filemanager/static/filemanager/')
FILEMANAGER_CKEDITOR_JS = getattr(settings, 'FILEMANAGER_CKEDITOR_JS',
                            'ckeditor/ckeditor.js')
