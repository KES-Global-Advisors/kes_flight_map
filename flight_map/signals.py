# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Activity

@receiver(post_save, sender=Activity)
def update_milestone_progress(sender, instance, **kwargs):
    if instance.milestone:
        # Save the parent milestone to trigger any recalculation logic in its save() method
        instance.milestone.save()
