# kes_flight_map/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def send_password_reset_email(email, reset_link):
    send_mail(
        subject="Password Reset Request",
        message=f"Click to reset password: {reset_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=f'<p>Click <a href="{reset_link}">here</a> to reset your password</p>'
    )