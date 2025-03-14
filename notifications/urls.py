# notifications/urls.py
from django.urls import path
from .views import NotificationListView, sse_notifications, mark_all_read, clear_notifications

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('sse/', sse_notifications, name='notification-sse'),
    path('mark-all-read/', mark_all_read, name='notification-mark-all-read'),
    path('clear/', clear_notifications, name='notification-clear'),
]
