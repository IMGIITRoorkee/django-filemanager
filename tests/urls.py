#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, patterns, url
from django.contrib import admin

from filemanager import path_end
from views import view

urlpatterns = patterns(
    url(r'^admin/', include(admin.site.urls)),
    url(r'^abc/' + path_end, view, name='view'),
)
