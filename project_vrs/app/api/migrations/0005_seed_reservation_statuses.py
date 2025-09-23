from django.db import migrations

HISTORY_STATUSES = {"CANCELLED", "COMPLETED", "NO_SHOW", "FAILED_PAYMENT"}
ACTIVE_STATUSES = {"PENDING_PAYMENT", "CONFIRMED", "ACTIVE"}


def seed_statuses(apps, schema_editor):
    ReservationStatus = apps.get_model("api", "ReservationStatus")

    all_statuses = HISTORY_STATUSES.union(ACTIVE_STATUSES)

    for status in all_statuses:
        ReservationStatus.objects.get_or_create(status=status)


def unseed_statuses(apps, schema_editor):
    ReservationStatus = apps.get_model("api", "ReservationStatus")
    all_statuses = HISTORY_STATUSES.union(ACTIVE_STATUSES)
    ReservationStatus.objects.filter(status__in=all_statuses).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_reservation_hold_expires_at"),
    ]

    operations = [
        migrations.RunPython(seed_statuses, reverse_code=unseed_statuses),
    ]
