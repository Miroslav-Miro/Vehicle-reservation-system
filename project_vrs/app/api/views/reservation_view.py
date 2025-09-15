from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..custom_permissions.mixed_role_permissions import RoleRequired
from django.utils.timezone import now
from django.db.models import Prefetch

from ..models import Reservation, PhysicalVehicleReservation, PhysicalVehicle, ReservationStatus
from ..serializers.reservation_serializer import (
    ReservationSerializer, CancelReservationSerializer
)
from rest_framework.decorators import action
from rest_framework import status as drf_status

class ReservationViewSet(viewsets.ModelViewSet):
    """
    This viewset lists all reservations for a user profile.
    It has two methods GET and PATCH.

    Detailed flow of the operations:

    1. Frotend with authentificated user (GET /api/user_reservations) 
    2. urls.py  ->  matches "api/user_reservations" 
    3. views.py (ReservationsViewSet)  ->  uses ReservationSerializer
    4. Returns query set for the current user (active or passed reservations)

    OR

    1. Frotend with authentificated user (PATCH /api/user_reservations) 
    2. urls.py  ->  matches "api/user_reservations" 
    3. views.py (ReservationsViewSet)  ->  uses CancelReservationSerializer
    4. Returns the updated reservation


    :param viewsets: The Django REST framework viewsets module.
    :type viewsets: module
    :return: _viewset instance_
    :rtype: _ViewSet_
    """

    serializer_class = ReservationSerializer
    http_method_names = ['get',"patch"]
    
    def get_permissions(self):
        """
        This method fetches the permissions for this viewset.

        :return: _list of permissions_
        :rtype: _list_
        """
        
        return [RoleRequired("user")]

    def get_queryset(self):
        """
        This method fetches the queryset of reservations.
        It filters reservations based on user_id (the logged user)
        and status query parameters. That way reservations can be filtered
        to show active or passed reservations.

        :return: _queryset of reservations
        :rtype: _QuerySet_
        """

        user_id = self.request.query_params.get("user_id")
        status = self.request.query_params.get("status")  
        qs = Reservation.objects.select_related(
            "status", "pickup_location", "dropoff_location", "user"
        ).prefetch_related(
            "physicalvehiclereservation_set__physical_vehicle__vehicle__brand",
            "physicalvehiclereservation_set__physical_vehicle__vehicle__model",
            "physicalvehiclereservation_set__physical_vehicle__vehicle__vehicle_type",
            "physicalvehiclereservation_set__physical_vehicle__vehicle__engine_type",
            "physicalvehiclereservation_set__physical_vehicle__location",
        )
        if user_id:
            qs = qs.filter(user_id=user_id)
        if status:
            if status.lower() == "history":
                qs = qs.filter(status__status__in=["cancelled", "completed"])
            else:
                qs = qs.filter(status__status__iexact=status)
        return qs
    
    def get_serializer_class(self):
        """
        This method fetches the serializer class for this viewset.
        It is different based on wheter the method is PATCH or not.
        Use CancelReservationSerializer only for PATCH

        :return: _serializer class_
        :rtype: django serializer class
        """

        if self.action == "partial_update":
            return CancelReservationSerializer
        return ReservationSerializer

    def partial_update(self, request, *args, **kwargs):
        """
        This method handles the PATCH request to update a reservation status.
        It only allows changing the status to "cancelled".


        :param request: _request object_
        :type request: HttpRequest
        :return: _response object_
        :rtype: HttpResponse
        """

        serializer = CancelReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        if new_status.lower() != "cancelled":
            return Response(
                {"detail": "You can only change status to 'cancelled'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        reservation = self.get_object()
        cancelled_status = ReservationStatus.objects.get(status__iexact="cancelled")
        reservation.status = cancelled_status
        reservation.save(update_fields=["status"])

        return Response(self.get_serializer(reservation).data)

