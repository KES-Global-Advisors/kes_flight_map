# notifications/signals.py
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from flight_map.models import Flightmap, Activity, Milestone, Strategy, Program, Workstream
from .models import Notification

# Utility function to send notifications to all Admin and Manager users
def notify_admin_manager(message, link, actor):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    recipients = User.objects.filter(role__in=['admin', 'manager'])
    for recipient in recipients:
        Notification.objects.create(
            recipient=recipient,
            actor=actor,
            message=message,
            link=link
        )

# --- Flightmap Creation Notification ---
@receiver(post_save, sender=Flightmap)
def notify_flightmap_created(sender, instance, created, **kwargs):
    if created:
        message = f"{instance.owner.username} created {instance.name} Flightmap"
        link = f"/flightmaps/{instance.id}/"  # Adjust URL as needed
        notify_admin_manager(message, link, actor=instance.owner)

# --- Activity Status Change Notification ---
@receiver(pre_save, sender=Activity)
def capture_activity_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Activity.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Activity.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Activity)
def notify_activity_status_change(sender, instance, created, **kwargs):
    if not created:
        old_status = getattr(instance, '_old_status', None)
        if old_status is not None and old_status != instance.status:
            actor = getattr(instance, 'updated_by', None)
            if instance.status == 'in_progress':
                message = f"{actor.username if actor else 'Someone'} marked {instance.name} as in progress"
            elif instance.status == 'completed':
                message = f"{actor.username if actor else 'Someone'} completed {instance.name}"
            else:
                message = f"{actor.username if actor else 'Someone'} updated {instance.name} to {instance.status}"
            link = f"/activities/{instance.id}/"
            notify_admin_manager(message, link, actor=actor)


# --- Milestone Status Change Notification ---
@receiver(pre_save, sender=Milestone)
def capture_milestone_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Milestone.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Milestone.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Milestone)
def notify_milestone_status_change(sender, instance, created, **kwargs):
    if not created:
        old_status = getattr(instance, '_old_status', None)
        if old_status is not None and old_status != instance.status:
            actor = getattr(instance, 'updated_by', None)
            if instance.status == 'completed':
                message = f"{actor.username if actor else 'Someone'} completed {instance.name}"
            elif instance.status == 'in_progress':
                message = f"{actor.username if actor else 'Someone'} marked {instance.name} as in progress"
            else:
                message = f"{actor.username if actor else 'Someone'} updated {instance.name} to {instance.status}"
            link = f"/milestones/{instance.id}/"
            notify_admin_manager(message, link, actor=actor)


# --- Membership Notifications via m2m_changed ---
# For Strategy: executive_sponsors, strategy_leads, communication_leads
@receiver(m2m_changed, sender=Strategy.executive_sponsors.through)
def notify_strategy_executive_sponsors(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(pk=user_id)
            message = f"You have been added as an Executive Sponsor to the strategy '{instance.name}'"
            link = f"/strategies/{instance.id}/"
            Notification.objects.create(
                recipient=user,
                actor=getattr(instance, 'owner', None),
                message=message,
                link=link
            )

@receiver(m2m_changed, sender=Strategy.strategy_leads.through)
def notify_strategy_leads(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(pk=user_id)
            message = f"You have been added as a Strategy Lead to the strategy '{instance.name}'"
            link = f"/strategies/{instance.id}/"
            Notification.objects.create(
                recipient=user,
                actor=getattr(instance, 'owner', None),
                message=message,
                link=link
            )

@receiver(m2m_changed, sender=Strategy.communication_leads.through)
def notify_strategy_communication_leads(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(pk=user_id)
            message = f"You have been added as a Communication Lead to the strategy '{instance.name}'"
            link = f"/strategies/{instance.id}/"
            Notification.objects.create(
                recipient=user,
                actor=getattr(instance, 'owner', None),
                message=message,
                link=link
            )

# For Program: executive_sponsors, program_leads, workforce_sponsors
@receiver(m2m_changed, sender=Program.executive_sponsors.through)
def notify_program_executive_sponsors(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(pk=user_id)
            message = f"You have been added as an Executive Sponsor to the program '{instance.name}'"
            link = f"/programs/{instance.id}/"
            Notification.objects.create(
                recipient=user,
                actor=getattr(instance.strategy, 'owner', None),
                message=message,
                link=link
            )

@receiver(m2m_changed, sender=Program.program_leads.through)
def notify_program_leads(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(pk=user_id)
            message = f"You have been added as a Program Lead to the program '{instance.name}'"
            link = f"/programs/{instance.id}/"
            Notification.objects.create(
                recipient=user,
                actor=getattr(instance.strategy, 'owner', None),
                message=message,
                link=link
            )

@receiver(m2m_changed, sender=Program.workforce_sponsors.through)
def notify_program_workforce_sponsors(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(pk=user_id)
            message = f"You have been added as a Workforce Sponsor to the program '{instance.name}'"
            link = f"/programs/{instance.id}/"
            Notification.objects.create(
                recipient=user,
                actor=getattr(instance.strategy, 'owner', None),
                message=message,
                link=link
            )

# For Workstream: workstream_leads, team_members
@receiver(m2m_changed, sender=Workstream.workstream_leads.through)
def notify_workstream_leads(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(pk=user_id)
            message = f"You have been added as a Workstream Lead to the workstream '{instance.name}'"
            link = f"/workstreams/{instance.id}/"
            Notification.objects.create(
                recipient=user,
                actor=getattr(instance.program.strategy, 'owner', None),
                message=message,
                link=link
            )

@receiver(m2m_changed, sender=Workstream.team_members.through)
def notify_workstream_team_members(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(pk=user_id)
            message = f"You have been added as a Team Member to the workstream '{instance.name}'"
            link = f"/workstreams/{instance.id}/"
            Notification.objects.create(
                recipient=user,
                actor=getattr(instance.program.strategy, 'owner', None),
                message=message,
                link=link
            )
