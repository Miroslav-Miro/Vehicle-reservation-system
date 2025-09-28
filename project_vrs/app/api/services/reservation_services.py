# # services/reservation_services.py
# from dataclasses import dataclass
# from datetime import datetime, time, timedelta
# from decimal import Decimal
# from typing import Optional, List, Dict

# from django.db import transaction
# from django.utils import timezone

# from ..models import (
#     Reservation, ReservationStatus,
#     PhysicalVehicle, PhysicalVehicleReservation,
#     Location,
# )

# HOLD_MINUTES = 15

# # Make sure these match exactly what's in your DB (case-insensitive works if you used __iexact elsewhere)
# BLOCKING_STATUSES = ("CONFIRMED", "ACTIVE", "PENDING_PAYMENT")

# @dataclass(frozen=True)
# class CreateReservationCommand:
#     user
#     start_date    # date
#     end_date      # date
#     lines: List[dict]                 # [{"vehicle_id": int, "qty": int}]
#     pickup_location_id: int           # required (we keep your simple design)
#     dropoff_location_id: Optional[int] = None


# @transaction.atomic
# def create_reservation_from_lines(cmd: CreateReservationCommand) -> Reservation:
#     # Day bounds (end is exclusive at 00:00 of end_date)
#     start = timezone.make_aware(datetime.combine(cmd.start_date, time.min))
#     end   = timezone.make_aware(datetime.combine(cmd.end_date,   time.min))
#     days = (cmd.end_date - cmd.start_date).days
#     if days < 1:
#         raise ValueError("Reservation must be at least 1 day.")

#     # Locations
#     pickup = Location.objects.filter(pk=cmd.pickup_location_id).first()
#     if not pickup:
#         raise ValueError("Invalid pickup_location_id.")
#     dropoff = (
#         Location.objects.filter(pk=cmd.dropoff_location_id).first()
#         if cmd.dropoff_location_id else pickup
#     )

#     # Merge duplicate conceptual lines
#     qty_by_vehicle: Dict[int, int] = {}
#     for line in cmd.lines:
#         vid = int(line["vehicle_id"])
#         qty_by_vehicle[vid] = qty_by_vehicle.get(vid, 0) + int(line["qty"])

#     # ---- NO-OVERLAP SELECTION (simple & safe) ----
#     chosen_units: List[PhysicalVehicle] = []
#     for vid, qty in qty_by_vehicle.items():
#         # Base: units of this conceptual vehicle at the pickup location
#         qs = PhysicalVehicle.objects.filter(
#             vehicle_id=vid, location_id=pickup.id
#         )

#         # Exclude units that are already reserved in the requested window
#         qs = qs.exclude(
#             physicalvehiclereservation__reservation__start_date__lt=end,
#             physicalvehiclereservation__reservation__end_date__gt=start,
#             physicalvehiclereservation__reservation__status__status__in=BLOCKING_STATUSES,
#         ).select_for_update(skip_locked=True).order_by("id")

#         count = qs.count()
#         if count < qty:
#             raise ValueError(
#                 f"Need {qty}, only {count} units of vehicle {vid} free at location {pickup.id} for those dates."
#             )

#         chosen_units.extend(list(qs[:qty]))
#     # -----------------------------------------------

#     # Status
#     pending = ReservationStatus.objects.get(status__iexact="PENDING_PAYMENT")

#     # Create reservation
#     res = Reservation.objects.create(
#         user=cmd.user,
#         start_date=start,
#         end_date=end,
#         status=pending,
#         total_price=Decimal("0.00"),
#         pickup_location=pickup,
#         dropoff_location=dropoff,
#     )

#     # Optional short hold
#     res.hold_expires_at = timezone.now() + timedelta(minutes=HOLD_MINUTES)
#     res.save(update_fields=["hold_expires_at"])

#     # Attach items & compute total
#     total = Decimal("0.00")
#     for u in chosen_units:
#         PhysicalVehicleReservation.objects.create(reservation=res, physical_vehicle=u)
#         total += u.vehicle.price_per_day * days

#     res.total_price = total
#     res.save(update_fields=["total_price"])
#     return res
