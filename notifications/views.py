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
from rest_framework_simplejwt.authentication import JWTAuthentication

# SSE endpoint to stream notifications in real time.
def sse_notifications(request):
    # Extract the token from the query parameters
    token = request.GET.get('token')
    if not token:
        return HttpResponse("Authentication credentials were not provided.", status=401)
    
    # Use JWTAuthentication to validate the token
    jwt_authenticator = JWTAuthentication()
    try:
        validated_token = jwt_authenticator.get_validated_token(token)
        user, validated_token = jwt_authenticator.get_user(validated_token), validated_token
        request.user = user
    except Exception as e:
        return HttpResponse("Invalid token.", status=401)
    
    # Now that the user is authenticated, we can stream notifications.
    last_id = 0  # starting point

    def event_stream():
        nonlocal last_id
        while True:
            notifications = Notification.objects.filter(
                recipient=request.user, id__gt=last_id
            ).order_by('id')
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


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_notifications(request):
    # Delete all notifications for the current user.
    deleted_count, _ = Notification.objects.filter(recipient=request.user).delete()
    return Response({'status': 'success', 'message': f'{deleted_count} notifications cleared.'})