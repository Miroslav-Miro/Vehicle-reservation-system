from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from ..models import (
    PhysicalVehicle,
    Reservation,
    PhysicalVehicleReservation,
    ReservationStatus,
)


class AvailabilityView(APIView):
    """
    API endpoint to get available cars for a given date range.

    Example:
    GET /api/availability start=2025-09-21 & end=2025-09-24
    """

    # permission_classes = [IsAuthenticated]

    def get(self, request):
        start = request.query_params.get("start")
        end = request.query_params.get("end")

        blocking_res_ids = Reservation.objects.filter(
            Q(status__in=["CONFIRMED", "ACTIVE"])
            | Q(status="PENDING_PAYMENT", hold_expires_at__gt=timezone.now())
        ).values_list("id", flat=True)

        overlapping_car_ids = PhysicalVehicleReservation.objects.filter(
            reservation_id__in=blocking_res_ids,
            reservation__start_date__lt=end,
            reservation__end_date__gt=start,
        ).values_list("physical_vehicle_id", flat=True)

        available = PhysicalVehicle.objects.exclude(id__in=overlapping_car_ids)

        data = [
            {
                "id": car.id,
                "plate": car.car_plate_number,
                "price_per_day": str(car.vehicle.price_per_day),
                "vehicle_model": car.vehicle.model.model_name,
                "brand": car.vehicle.model.brand.brand_name,
            }
            for car in available
        ]
        return Response({"available": data})
