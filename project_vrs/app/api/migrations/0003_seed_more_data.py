# api/migrations/0003_seed_more_data.py
from django.db import migrations
from decimal import Decimal
from django.utils import timezone
import datetime
import random


def seed_more_data(apps, schema_editor):
    # Historical models
    Brand = apps.get_model("api", "Brand")
    Model = apps.get_model("api", "Model")
    EngineType = apps.get_model("api", "EngineType")
    VehicleType = apps.get_model("api", "VehicleType")
    Vehicle = apps.get_model("api", "Vehicle")
    PhysicalVehicle = apps.get_model("api", "PhysicalVehicle")
    User = apps.get_model("api", "User")
    Role = apps.get_model("api", "Role")
    Location = apps.get_model("api", "Location")
    ReservationStatus = apps.get_model("api", "ReservationStatus")
    Reservation = apps.get_model("api", "Reservation")
    PhysicalVehicleReservation = apps.get_model("api", "PhysicalVehicleReservation")
    LoginEvent = apps.get_model("api", "LoginEvent")

    # ---- Helper: get role / statuses / locations we rely on (from your initial seed) ----
    user_role = Role.objects.filter(role_name__iexact="user").first()
    if not user_role:
        # Fallback: first role
        user_role = Role.objects.first()

    # statuses you already created: "active", "cancelled", "completed"
    status_active = ReservationStatus.objects.filter(status__iexact="active").first()
    status_completed = ReservationStatus.objects.filter(status__iexact="completed").first()
    status_cancelled = ReservationStatus.objects.filter(status__iexact="cancelled").first()
    statuses = [s for s in [status_active, status_completed, status_cancelled] if s]

    all_locations = list(Location.objects.all())
    if not all_locations:
        # We don't create locations here (your other migration does).
        # If none exist, we can't seed physical vehicles/reservations reliably.
        return

    # ---- Engine Types (≥10) ----
    engine_types = [
        "Petrol I3", "Petrol I4", "Petrol V6", "Diesel I4", "Diesel V6",
        "Hybrid HEV", "Hybrid PHEV", "Electric RWD", "Electric AWD", "LPG"
    ]
    engine_map = {}
    for name in engine_types:
        et, _ = EngineType.objects.get_or_create(engine_type=name)
        engine_map[name] = et

    # ---- Vehicle Types (≥10) ----
    vehicle_types = [
        "Sedan", "Hatchback", "SUV", "Crossover", "Coupe",
        "Convertible", "Wagon", "Van", "Pickup", "Minivan"
    ]
    vtype_map = {}
    for name in vehicle_types:
        vt, _ = VehicleType.objects.get_or_create(vehicle_type=name)
        vtype_map[name] = vt

    # ---- Brands (≥10) ----
    brand_names = [
        "Toyota", "BMW", "Mercedes-Benz", "Audi", "Volkswagen",
        "Ford", "Honda", "Nissan", "Kia", "Hyundai"
    ]
    brand_map = {}
    for bname in brand_names:
        b, _ = Brand.objects.get_or_create(brand_name=bname)
        brand_map[bname] = b

    # ---- Models (≥10, mapped to brands) ----
    # At least one model per brand; overall ≥10 models total
    brand_models = {
        "Toyota": ["Corolla", "Camry"],
        "BMW": ["3 Series", "X3"],
        "Mercedes-Benz": ["C-Class", "GLA"],
        "Audi": ["A4", "Q3"],
        "Volkswagen": ["Golf", "Passat"],
        "Ford": ["Focus", "Kuga"],
        "Honda": ["Civic", "CR-V"],
        "Nissan": ["Qashqai", "Altima"],
        "Kia": ["Sportage", "Ceed"],
        "Hyundai": ["Elantra", "Tucson"],
    }
    model_map = {}
    for bname, models in brand_models.items():
        b = brand_map[bname]
        for mname in models:
            m, _ = Model.objects.get_or_create(brand=b, model_name=mname)
            model_map[(bname, mname)] = m

    # ---- Users (≥10) ----
    # We'll mark seeded users with a pattern to cleanly reverse.
    seeded_users = []
    for i in range(1, 11):
        username = f"seed_user{i}"
        email = f"seed_user{i}@example.com"
        # create bare instance, then set_password (available on AbstractBaseUser models)
        if not User.objects.filter(username=username).exists():
            u = User(
                username=username,
                email=email,
                first_name=f"Seed{i}",
                last_name="User",
                address="Seed Street 1",
                date_of_birth=datetime.date(1990, 1, min(28, i)),  # 1990-01-01..-28
                phone_number=f"+359000000{i:02d}",
                is_active=True,
                is_staff=False,
                is_blocked=False,
                role_id=user_role,
            )
            # set_password is safe to call in data migrations
            try:
                u.set_password("Passw0rd!")
            except Exception:
                # If set_password is not available for any reason, store raw (not recommended)
                u.password = "Passw0rd!"
            u.save()
            seeded_users.append(u)
        else:
            seeded_users.append(User.objects.get(username=username))

    # ---- Vehicles (≥10)
    # Create one conceptual Vehicle per model above (=> 20) with reasonable data
    all_engine_types = list(engine_map.values())
    all_vehicle_types = list(vtype_map.values())

    vehicles = []
    seat_options = [4, 5, 5, 5, 7]  # common seat counts
    base_prices = {
        "Sedan": Decimal("40.00"),
        "Hatchback": Decimal("35.00"),
        "SUV": Decimal("55.00"),
        "Crossover": Decimal("50.00"),
        "Coupe": Decimal("60.00"),
        "Convertible": Decimal("75.00"),
        "Wagon": Decimal("45.00"),
        "Van": Decimal("65.00"),
        "Pickup": Decimal("70.00"),
        "Minivan": Decimal("60.00"),
    }

    for (bname, mname), mdl in model_map.items():
        # rotate type and engine for variety
        vt = random.choice(all_vehicle_types)
        et = random.choice(all_engine_types)
        seats = random.choice(seat_options)
        price = base_prices.get(vt.vehicle_type, Decimal("50.00"))
        # small random jitter
        price = price + Decimal(random.randint(-5, 8))

        v, _ = Vehicle.objects.get_or_create(
            model=mdl,
            brand=brand_map[bname],
            vehicle_type=vt,
            engine_type=et,
            defaults={"amount_seats": seats, "price_per_day": price},
        )
        # If existed, ensure amount/price (don’t override blindly)
        if _ is False:
            if not v.amount_seats:
                v.amount_seats = seats
            if not v.price_per_day:
                v.price_per_day = price
            v.save()
        vehicles.append(v)

    # Ensure at least 10
    if len(vehicles) < 10:
        # If something odd happened, clone some entries with slight changes
        for i in range(10 - len(vehicles)):
            any_mdl = next(iter(model_map.values()))
            vt = random.choice(all_vehicle_types)
            et = random.choice(all_engine_types)
            v = Vehicle.objects.create(
                model=any_mdl,
                brand=any_mdl.brand,
                vehicle_type=vt,
                engine_type=et,
                amount_seats=random.choice(seat_options),
                price_per_day=Decimal("49.00") + Decimal(i),
            )
            vehicles.append(v)

    # ---- Physical Vehicles (≥10)
    # Create ~3 units per conceptual vehicle, spread across locations
    phys_units = []
    plate_counter = 1
    for v in vehicles:
        for _ in range(3):
            loc = random.choice(all_locations)
            plate = f"SEED-{v.id:03d}-{plate_counter:03d}"
            pv, _ = PhysicalVehicle.objects.get_or_create(
                vehicle=v,
                location=loc,
                car_plate_number=plate,
            )
            phys_units.append(pv)
            plate_counter += 1

    # Ensure at least 10 physical vehicles
    if len(phys_units) < 10:
        for i in range(10 - len(phys_units)):
            loc = random.choice(all_locations)
            v = random.choice(vehicles)
            plate = f"SEED-EXTRA-{i:03d}"
            pv = PhysicalVehicle.objects.create(
                vehicle=v, location=loc, car_plate_number=plate
            )
            phys_units.append(pv)

    # ---- Reservations (≥10) and PhysicalVehicleReservations
    # We'll create overlapping and non-overlapping ranges in the near future/past
    seeded_reservations = []
    now = timezone.now()
    for i in range(12):
        user = random.choice(seeded_users)
        pv = random.choice(phys_units)
        days = random.randint(2, 7)
        start = now + datetime.timedelta(days=random.randint(-10, 20))
        end = start + datetime.timedelta(days=days)
        status = random.choice(statuses) if statuses else None

        total = (pv.vehicle.price_per_day or Decimal("50.00")) * days

        r = Reservation.objects.create(
            user=user,
            status=status,
            total_price=total,
            start_date=start,
            end_date=end,
            pickup_location=pv.location,
            dropoff_location=random.choice(all_locations),
        )
        PhysicalVehicleReservation.objects.create(
            physical_vehicle=pv,
            reservation=r,
        )
        seeded_reservations.append(r)

    # ---- Login events (≥10)
    for i, user in enumerate(seeded_users):
        LoginEvent.objects.create(
            user=user,
            event_type="LOGIN_SUCCESS",
            ip_address=f"10.0.0.{i+1}",
            user_agent="SeedAgent/1.0",
        )


def unseed_more_data(apps, schema_editor):
    Brand = apps.get_model("api", "Brand")
    Model = apps.get_model("api", "Model")
    EngineType = apps.get_model("api", "EngineType")
    VehicleType = apps.get_model("api", "VehicleType")
    Vehicle = apps.get_model("api", "Vehicle")
    PhysicalVehicle = apps.get_model("api", "PhysicalVehicle")
    User = apps.get_model("api", "User")
    Reservation = apps.get_model("api", "Reservation")
    PhysicalVehicleReservation = apps.get_model("api", "PhysicalVehicleReservation")
    LoginEvent = apps.get_model("api", "LoginEvent")

    # Delete in dependency order (children first)
    # Identify seeded data by markers (names and plate prefixes / usernames)
    LoginEvent.objects.filter(user__username__startswith="seed_user").delete()
    PhysicalVehicleReservation.objects.filter(
        physical_vehicle__car_plate_number__startswith="SEED-"
    ).delete()
    Reservation.objects.filter(user__username__startswith="seed_user").delete()
    PhysicalVehicle.objects.filter(car_plate_number__startswith="SEED-").delete()
    Vehicle.objects.filter(model__model_name__in=[
        "Corolla","Camry","3 Series","X3","C-Class","GLA","A4","Q3",
        "Golf","Passat","Focus","Kuga","Civic","CR-V","Qashqai","Altima",
        "Sportage","Ceed","Elantra","Tucson"
    ]).delete()
    # core reference tables seeded here
    EngineType.objects.filter(engine_type__in=[
        "Petrol I3","Petrol I4","Petrol V6","Diesel I4","Diesel V6",
        "Hybrid HEV","Hybrid PHEV","Electric RWD","Electric AWD","LPG"
    ]).delete()
    VehicleType.objects.filter(vehicle_type__in=[
        "Sedan","Hatchback","SUV","Crossover","Coupe","Convertible",
        "Wagon","Van","Pickup","Minivan"
    ]).delete()
    Model.objects.filter(model_name__in=[
        "Corolla","Camry","3 Series","X3","C-Class","GLA","A4","Q3",
        "Golf","Passat","Focus","Kuga","Civic","CR-V","Qashqai","Altima",
        "Sportage","Ceed","Elantra","Tucson"
    ]).delete()
    Brand.objects.filter(brand_name__in=[
        "Toyota","BMW","Mercedes-Benz","Audi","Volkswagen",
        "Ford","Honda","Nissan","Kia","Hyundai"
    ]).delete()
    User.objects.filter(username__startswith="seed_user").delete()


class Migration(migrations.Migration):

    dependencies = [
        # Change this to your last migration 
        ("api", "0002_seed_initial_data"),
    ]

    operations = [
        migrations.RunPython(seed_more_data, reverse_code=unseed_more_data),
    ]
