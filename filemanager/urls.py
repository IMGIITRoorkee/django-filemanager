from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.decorators import user_passes_test

from . import views

staff_required = user_passes_test(lambda u: u.is_staff)


urlpatterns = [
    url(r'^(?P<path>[\w -/.]*)$',
        staff_required(views.FileManager.as_view(basepath=settings.MEDIA_ROOT))
        ),
]
