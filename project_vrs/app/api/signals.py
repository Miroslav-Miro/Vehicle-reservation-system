from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction

from .models import Reservation
from .email_sender.tasks import (
    send_reservation_created_email,
    send_reservation_status_changed_email,
)


@receiver(pre_save, sender=Reservation)
def _remember_old_status(sender, instance: Reservation, **kwargs):
    """
    Store the old status PK on the instance before saving (for change comparison)
    """
    if not instance.pk:
        instance._old_status_id = None
        return
    try:
        old = sender.objects.only("status").get(pk=instance.pk)
        instance._old_status_id = old.status_id
    except sender.DoesNotExist:
        instance._old_status_id = None


@receiver(post_save, sender=Reservation)
def _enqueue_notifications(sender, instance: Reservation, created: bool, **kwargs):
    """
    After save, enqueue tasks AFTER the transaction commits
    """

    def on_commit():
        if created:
            send_reservation_created_email.delay(instance.id)
            return
        old_status_id = getattr(instance, "_old_status_id", None)
        if old_status_id != instance.status_id:
            send_reservation_status_changed_email.delay(
                instance.id, old_status_id, instance.status_id
            )

    transaction.on_commit(on_commit)
