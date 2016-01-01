from django.conf import settings
from django.conf.urls import url

from . import views

path_end = r'(?P<path>[\w -/.]*)$'


urlpatterns = [
    url(r'^' + path_end, views.FileManager.as_view(basepath=settings.MEDIA_ROOT)),
]
