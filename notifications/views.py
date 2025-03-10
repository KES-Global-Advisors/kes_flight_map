# notifications/views.py
from django.shortcuts import render
import time
import json
from django.http import StreamingHttpResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

# SSE endpoint to stream notifications in real time.
@login_required
def sse_notifications(request):
    last_id = 0  # starting point; you might alternatively allow a query parameter for last seen ID

    def event_stream():
        nonlocal last_id
        while True:
            # Get notifications with IDs greater than the last sent
            notifications = Notification.objects.filter(recipient=request.user, id__gt=last_id).order_by('id')
            for notification in notifications:
                serializer = NotificationSerializer(notification)
                data = json.dumps(serializer.data)
                yield f"data: {data}\n\n"
                last_id = notification.id
            # Heartbeat to keep the connection alive
            yield ":\n\n"
            time.sleep(5)  # Adjust the sleep interval as needed

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

# API view to list notifications
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    # Mark all unread notifications for the authenticated user as read.
    Notification.objects.filter(recipient=request.user, read=False).update(read=True)
    return Response({'status': 'success', 'message': 'All notifications marked as read.'})