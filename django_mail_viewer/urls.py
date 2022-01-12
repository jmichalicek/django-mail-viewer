from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r'message/(?P<message_id>.+)/attachment/(?P<attachment>.+)/$',
        views.EmailAttachmentDownloadView.as_view(),
        name="mail_viewer_attachment",
    ),
    re_path(r'message/(?P<message_id>.+)/delete/$', views.EmailDeleteView.as_view(), name="mail_viewer_delete"),
    re_path(r'message/(?P<message_id>.+)/$', views.EmailDetailView.as_view(), name='mail_viewer_detail'),
    re_path(r'', views.EmailListView.as_view(), name='mail_viewer_list'),
]
