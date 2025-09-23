from logging import getLogger
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Prefetch
from ..models import Reservation, PhysicalVehicleReservation, ReservationStatus

logger = getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def send_reservation_created_email(self, reservation_id: int) -> None:
    """
    Send a 'reservation created' email.
    """
    try:
        reservation = Reservation.objects.select_related("user").get(pk=reservation_id)
    except Reservation.DoesNotExist:
        logger.warning("Email skipped: reservation %s not found.", reservation_id)
        return

    ctx = {
        "reservation": reservation,
        "user": reservation.user,
        "vehicles": [
            pvr.physical_vehicle
            for pvr in reservation.physicalvehiclereservation_set.all()
        ],
    }

    subject = render_to_string("email/reservation_created_subject.txt", ctx).strip()
    body_txt = render_to_string("email/reservation_created.txt", ctx)
    body_html = render_to_string("email/reservation_created.html", ctx)

    send_mail(
        subject,
        body_txt,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.user.email],
        html_message=body_html,
        fail_silently=False,
    )


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def send_reservation_status_changed_email(
    self, reservation_id: int, old_status_id: int | None, new_status_id: int
) -> None:
    """
    Sends an email whenever a reservation's status changes.
    """
    reservation = (
        Reservation.objects.select_related("user", "status")
        .prefetch_related(
            Prefetch(
                "physicalvehiclereservation_set",
                queryset=PhysicalVehicleReservation.objects.select_related(
                    "physical_vehicle"
                ),
            )
        )
        .get(pk=reservation_id)
    )

    old_label = (
        ReservationStatus.objects.get(pk=old_status_id).status if old_status_id else "—"
    )
    new_label = reservation.status.status

    ctx = {
        "reservation": reservation,
        "user": reservation.user,
        "old_status": old_label,
        "new_status": new_label,
        "vehicles": [
            pvr.physical_vehicle
            for pvr in reservation.physicalvehiclereservation_set.all()
        ],
    }

    subject = render_to_string("email/reservation_status_subject.txt", ctx).strip()
    body_txt = render_to_string("email/reservation_status.txt", ctx)
    body_html = render_to_string("email/reservation_status.html", ctx)

    send_mail(
        subject,
        body_txt,
        settings.DEFAULT_FROM_EMAIL,
        [reservation.user.email],
        html_message=body_html,
        fail_silently=False,
    )
