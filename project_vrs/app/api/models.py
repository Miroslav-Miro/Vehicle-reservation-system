from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, F


class Role(models.Model):
    """
    The class represents the role of the user -
    admin, manager or user

    :param models: The Django models module.
    :type models: module
    :return: the role name
    :rtype: str
    """

    role_name = models.CharField(max_length=30)

    def __str__(self):
        return self.role_name
class UserManager(BaseUserManager):
    """
    Custom manager for the User model, extending Django's BaseUserManager.

    This class provides helper methods to create regular users and superusers.
    It enforces required fields (username, email, password) and ensures proper
    defaults for superusers. It also normalizes email addresses before saving.

    create_superuser(username, email, password=None, **extra_fields):


    :param BaseUserManager: BseUserManager
    :type BaseUserManager: class
    """

    def create_user(self, username, email, password=None, **extra_fields):
        """
        Creates and saves a regular user with the given username, email,
        password, and any additional fields.

        :param username: username of the user
        :type username: str
        :param email: email of the user
        :type email: str
        :param password: password of the user, defaults to None
        :type password: string, optional
        :raises ValueError: If email is not set
        :raises ValueError: If username is not set
        :raises ValueError: Is password is not set
        :return: the user object
        :rtype: User instance
        """

        if not email:
            raise ValueError("The Email field must be set")
        if not username:
            raise ValueError("The Username field must be set")
        if not password:
            raise ValueError("A password is required")
        email = self.normalize_email(email)
        user = self.model(
            username=username, email=email, **extra_fields
        )  ## Creates the user
        user.set_password(password)  ## Sets the password of the created user
        user.save(using=self._db)  ## Saves the user to the database

        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given username, email,
        password, and any additional fields. Ensures the user is marked
        as staff, active, and superuser, and assigns the "admin" role if it exists.

        :param username: username of the user
        :type username: str
        :param email: email of the user
        :type email: str
        :param password: password of the user, defaults to None
        :type password: string, optional
        :raises ValueError: If admin role doesn't exist in the db
        :return: the user object
        :rtype: User instance
        """

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if "role_id" not in extra_fields:
            try:
                from .models import Role

                extra_fields["role_id"] = Role.objects.get(role_name="admin")
            except:
                raise ValueError("Admin role must exist before creating a superuser.")

        ##Providing a defualt date_of_birth for superuser creation to avoid errors.
        return self.create_user(
            username, email, password, date_of_birth="2000-01-01", **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that replaces Django's default User.

    This model is built on top of AbstractBaseUser and PermissionsMixin
    to provide full control over authentication fields and permissions.
    It includes common user details, role-based access, and support for
    Django's authentication system.

    :param AbstractBaseUser: AbstractBaseUser
    :type AbstractBaseUser: class
    :param PermissionsMixin: PermissionsMixin
    :type PermissionsMixin: class
    """

    username = models.CharField(
        max_length=150, unique=True, validators=[UnicodeUsernameValidator()]
    )
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

    role_id = models.ForeignKey(Role, on_delete=models.PROTECT)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]


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
    Represents the brand of the vehicle - Mercedes, BMW, etc.

    :param models: The Django models module.
    :type models: module
    """

    brand_name = models.CharField(max_length=30)

    def __str__(self):
        return self.brand_name


class Model(models.Model):
    """
    Represents the brand of the vehicle.
    For example Golf 5 for VW or Avensis for Toyota.

    :param models: The Django models module.
    :type models: module
    """

    model_name = models.CharField(max_length=50)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)

    def __str__(self):
        return self.model_name


class EngineType(models.Model):
    """
    Represents the engine type of the vehicle.
    For example gasoline or diesel.

    :param models: The Django models module.
    :type models: module
    """

    engine_type = models.CharField(max_length=40)

    def __str__(self):
        return self.engine_type


class VehicleType(models.Model):
    """
    Represents the vehicle type

    :param models: The Django models module.
    :type models: module
    """

    vehicle_type = models.CharField(max_length=40)

    def __str__(self):
        return self.vehicle_type


class Vehicle(models.Model):
    """
    Represents a vehicle as a conceptual model.

    :param models: The Django models module.
    :type models: module
    """

    amount_seats = models.CharField(max_length=10)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.CASCADE)
    engine_type = models.ForeignKey(EngineType, on_delete=models.CASCADE)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)

class Location(models.Model):
    """
    Represents a location of a vehicle or office.

    :param models: The Django models module.
    :type models: module
    """

    ##a city or village
    location_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)

class PhysicalVehicle(models.Model):
    """
    Represents a vehicle as a physical instance,
    each physcal vehicle has a conceptual model (Vehicle).

    :param models: The Django models module.
    :type models: module
    """

    car_plate_number = models.CharField(max_length=20, unique=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)

class ReservationStatus(models.Model):
    """
    Represents the status of a reservation.

    :param models: The Django models module.
    :type models: module
    """

    status = models.CharField(max_length=30)


class Reservation(models.Model):
    """
    Represents a reservation made by a user.

    :param models: The Django models module.
    :type models: module
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.ForeignKey(ReservationStatus, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    pickup_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='pickup_location')
    dropoff_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='dropoff_location')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PhysicalVehicleReservation(models.Model):
    """
    Represents the reservation of a specific physical vehicle
    in a particular reservation.

    :param models: The Django models module.
    :type models: module
    """

    physical_vehicle = models.ForeignKey(PhysicalVehicle, on_delete=models.CASCADE)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)