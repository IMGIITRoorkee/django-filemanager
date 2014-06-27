from django.conf import settings

FILEMANAGER_STATIC_ROOT = getattr(settings, 'FILEMANAGER_STATIC_ROOT',
                            'filemanager/static/filemanager/')
FILEMANAGER_CKEDITOR_JS = getattr(settings, 'FILEMANAGER_CKEDITOR_JS',
                            'ckeditor/ckeditor.js')
FILEMANAGER_CHECK_SPACE = getattr(settings, 'FILEMANAGER_CHECK_SPACE',
                            False)
FILEMANAGER_SHOW_SPACE = getattr(settings, 'FILEMANAGER_SHOW_SPACE',
                            FILEMANAGER_CHECK_SPACE)
