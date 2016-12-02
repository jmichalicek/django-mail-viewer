# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'message/(?P<message_id>.+)/attachment/(?P<attachment>.+)/',
        views.EmailAttachmentDownloadView.as_view(), name="mail_viewer_attachment"),
    url(r'message/(?P<message_id>.+)/', views.EmailDetailView.as_view(), name='mail_viewer_detail'),
    url(r'', views.EmailListView.as_view(), name='mail_viewer_list'),
    ]
