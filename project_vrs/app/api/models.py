from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)
from django.contrib.auth.validators import UnicodeUsernameValidator

class Role(models.Model):
    role_name = models.CharField(max_length=30)

class UserManager(BaseUserManager):
    def create_user(self,username,email,password=None,**extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
        if not password:
            raise ValueError("A password is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields) ## Creates the user
        user.set_password(password) ## Sets the password of the created user
        user.save(using=self._db) ## Saves the user to the database

        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault("is_active", True)
        if 'role_id' not in extra_fields:
            try:
                from .models import Role
                extra_fields['role_id'] = Role.objects.get(role_name="admin")
            except:
                raise ValueError("Admin role must exist before creating a superuser.")


        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser,PermissionsMixin):
    username = models.CharField(max_length=150, unique=True, validators=[UnicodeUsernameValidator()])
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    phone_number = models.CharField(max_length=15)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    role_id = models.ForeignKey(Role, on_delete=models.CASCADE)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

class LoginEvent(models.Model):
    EVENT_TYPES = [
        ("LOGIN_SUCCESS", "Login Success"),
        ("LOGIN_FAILED", "Login Failed"),
        ("LOGOUT", "Logout"),
        ("ACCOUNT_LOCK", "Account Locked"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.event_type} @ {self.timestamp}"

class Brand(models.Model):
    """
    Represents the brand of the vehicle.

    :param models: The Django models module.
    :type models: module
    """
    brand_name = models.CharField(max_length=30)

class Model(models.Model):
    model_name = models.CharField(max_length=50)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)

class EngineType(models.Model):
    engine_type = models.CharField(max_length=40)

class VehicleType(models.Model):
    vehicle_type = models.CharField(max_length=40)

class Vehicle(models.Model):
    car_plate_number = models.CharField(max_length=20, unique=True)
    amount_seats = models.CharField(max_length=10)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE)
    engine_type = models.ForeignKey(EngineType, on_delete=models.CASCADE)
    models = models.ForeignKey(Model, on_delete=models.CASCADE)

class ReservationStatus(models.Model):
    status = models.CharField(max_length=30)
class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.ForeignKey(ReservationStatus, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class VehicleReservation(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

