# -*- coding: utf-8 -*-
from django.conf.urls import patterns
from django.conf.urls import include
from django.conf.urls import url

from sharing.views import SelectExtensionView


urlpatterns = patterns('',
    url(
        r'^sample/(?P<sha256>[\w]+)$',
        SelectExtensionView,
        name='sharing.select.extension'
    )
)
