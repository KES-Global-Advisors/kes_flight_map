# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Activity

@receiver(post_save, sender=Activity)
def update_milestone_progress(sender, instance, **kwargs):
    # Update source milestone progress (this is where progress is calculated from)
    if instance.source_milestone:
        # Save the source milestone to trigger any recalculation logic in its save() method
        instance.source_milestone.save()
    
    # Also update target milestone if it's different from source
    if instance.target_milestone and instance.target_milestone != instance.source_milestone:
        instance.target_milestone.save()