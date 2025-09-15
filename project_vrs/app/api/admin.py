from django.contrib import admin
from .models import (
    Role, User, Brand, Model, EngineType, VehicleType,
    Vehicle, PhysicalVehicle, ReservationStatus, Reservation, PhysicalVehicleReservation
)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "role_name")
    search_fields = ("role_name",)
    ordering = ("role_name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "first_name", "last_name", "role_id", "is_active", "is_staff", "is_blocked")
    list_filter = ("is_active", "is_staff", "is_blocked", "role_id")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    readonly_fields = ("created_at", "updated_at")

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "brand_name")
    search_fields = ("brand_name",)
    ordering = ("brand_name",)


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ("id", "model_name", "brand")
    list_filter = ("brand",)
    search_fields = ("model_name", "brand__brand_name")
    ordering = ("brand__brand_name", "model_name")


@admin.register(EngineType)
class EngineTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "engine_type")
    search_fields = ("engine_type",)
    ordering = ("engine_type",)


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "vehicle_type")
    search_fields = ("vehicle_type",)
    ordering = ("vehicle_type",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("id", "brand", "model", "vehicle_type", "engine_type", "amount_seats", "price_per_day")
    list_filter = ("vehicle_type", "engine_type", "brand")
    search_fields = ("model__model_name", "brand__brand_name")
    ordering = ("brand__brand_name", "model__model_name")


@admin.register(PhysicalVehicle)
class PhysicalVehicleAdmin(admin.ModelAdmin):
    list_display = ("id", "car_plate_number", "vehicle", "location")
    search_fields = ("car_plate_number", "vehicle__model__model_name", "vehicle__brand__brand_name")
    ordering = ("car_plate_number",)


# ============ Reservations ============
@admin.register(ReservationStatus)
class ReservationStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "status")
    search_fields = ("status",)
    ordering = ("status",)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_price", "start_date", "end_date", "created_at", "updated_at")
    list_filter = ("status", "created_at", "start_date", "end_date")
    search_fields = ("user__username", "user__email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(PhysicalVehicleReservation)
class PhysicalVehicleReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "physical_vehicle", "reservation", "reservation_start", "reservation_end", "reservation_price")
    list_filter = ("reservation__start_date", "reservation__end_date", "physical_vehicle")
    search_fields = ("physical_vehicle__car_plate_number", "reservation__user__username")
    ordering = ("-reservation__start_date",)

    def reservation_start(self, obj):
        return obj.reservation.start_date
    reservation_start.admin_order_field = "reservation__start_date"
    reservation_start.short_description = "Start Date"

    def reservation_end(self, obj):
        return obj.reservation.end_date
    reservation_end.admin_order_field = "reservation__end_date"
    reservation_end.short_description = "End Date"

    def reservation_price(self, obj):
        return obj.reservation.total_price
    reservation_price.admin_order_field = "reservation__total_price"
    reservation_price.short_description = "Total Price"
