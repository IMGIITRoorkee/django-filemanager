#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import unicode_literals

from django.conf import settings
from filemanager import FileManager


def view(request, path):
    extensions = ['html', 'htm', 'zip', 'py', 'css', 'js', 'jpeg', 'jpg', 'png']
    fm = FileManager(settings.MEDIA_ROOT, extensions=extensions)
    return fm.render(request, path)
