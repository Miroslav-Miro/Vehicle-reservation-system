from django.db import migrations


def seed_vehicle_data(apps, schema_editor):
    """
    Seeds initial vehicle related data into the database.

    This includes:
      - Brands (BMW, Mercedes, Toyota, Volkswagen)
      - Models (linked to their brands)
      - Engine types (Diesel, Gasoline, Hybrid, Electric)
      - Vehicle types (Sedan, SUV, Hatchback, Coupe)
      - Vehicles (vehicles with seats, price, type, engine, model, brand)
      - Physical vehicles (instances with license plate, linked to vehicles and locations)

    The purpose of the function is to provide demo/test data so that the
    system can be used immediately after setup, without requiring manual inserts
    """

    # Get models from historical version (apps.get_model ensures compatibility)
    Brand = apps.get_model("api", "Brand")
    Model = apps.get_model("api", "Model")
    EngineType = apps.get_model("api", "EngineType")
    VehicleType = apps.get_model("api", "VehicleType")
    Vehicle = apps.get_model("api", "Vehicle")
    PhysicalVehicle = apps.get_model("api", "PhysicalVehicle")
    Location = apps.get_model("api", "Location")

    # Seed Brands
    brands = ["BMW", "Mercedes", "Toyota", "Volkswagen"]
    brand_objects = {}
    for b in brands:
        # get_or_create ensures we don’t duplicate on re-run
        brand, _ = Brand.objects.get_or_create(brand_name=b)
        brand_objects[b] = brand

    # Seed Models
    models = [
        ("3 Series", "BMW"),
        ("C-Class", "Mercedes"),
        ("Avensis", "Toyota"),
        ("Golf 5", "Volkswagen"),
    ]
    model_objects = {}
    for model_name, brand_name in models:
        model, _ = Model.objects.get_or_create(
            model_name=model_name, brand=brand_objects[brand_name]
        )
        model_objects[model_name] = model

    # Seed EngineType
    engine_types = ["Diesel", "Gasoline", "Hybrid", "Electric"]
    engine_objects = {}
    for e in engine_types:
        et, _ = EngineType.objects.get_or_create(engine_type=e)
        engine_objects[e] = et

    # Seed VehicleTypes
    vehicle_types = ["Sedan", "SUV", "Hatchback", "Coupe"]
    vehicle_type_objects = {}
    for vt in vehicle_types:
        vto, _ = VehicleType.objects.get_or_create(vehicle_type=vt)
        vehicle_type_objects[vt] = vto

    # Seed Vehicles
    vehicles = [
        (5, 100.00, "Sedan", "Diesel", "3 Series", "BMW"),
        (5, 120.00, "Sedan", "Gasoline", "C-Class", "Mercedes"),
        (5, 80.00, "Sedan", "Diesel", "Avensis", "Toyota"),
        (5, 70.00, "Hatchback", "Gasoline", "Golf 5", "Volkswagen"),
    ]
    vehicle_objects = {}
    for seats, price, vt, et, model, brand in vehicles:
        v, _ = Vehicle.objects.get_or_create(
            amount_seats=seats,
            price_per_day=price,
            vehicle_type=vehicle_type_objects[vt],
            engine_type=engine_objects[et],
            model=model_objects[model],
            brand=brand_objects[brand],
        )
        vehicle_objects[f"{brand}-{model}"] = v

    # Seed Physical Vehicles (a real instances with license plate)
    # Locations are already created in 0002_seed_initial_data
    locations = list(Location.objects.all())
    physicals = [
        ("CA1234AB", "BMW-3 Series", locations[0]),
        ("CB5678AB", "Mercedes-C-Class", locations[1]),
        ("PB1111KT", "Toyota-Avensis", locations[2]),
        ("PA1234MA", "Volkswagen-Golf 5", locations[3]),
    ]
    for plate, vehicle_key, location in physicals:
        PhysicalVehicle.objects.get_or_create(
            car_plate_number=plate,
            vehicle=vehicle_objects[vehicle_key],
            location=location,
        )


def unseed_vehicle_data(apps, schema_editor):
    """
    Removes the seeded vehicle-related data.

    This function performs the reverse of seed_vehicle_data()
    It deletes:
      - Physical vehicles (by plate number)
      - Vehicles
      - Engine types
      - Vehicle types
      - Models
      - Brands

    The goal is to keep the database clean if this migration is rolled back.
    """

    Brand = apps.get_model("api", "Brand")
    Model = apps.get_model("api", "Model")
    EngineType = apps.get_model("api", "EngineType")
    VehicleType = apps.get_model("api", "VehicleType")
    Vehicle = apps.get_model("api", "Vehicle")
    PhysicalVehicle = apps.get_model("api", "PhysicalVehicle")

    # Delete seeded physical vehicles
    PhysicalVehicle.objects.filter(
        car_plate_number__in=["CA1234AB", "CB5678CD", "PB1111TT", "B1234VV"]
    ).delete()

    # Delete conceptual vehicles
    Vehicle.objects.all().delete()

    # Delete engine types and vehicle types
    EngineType.objects.filter(
        engine_type__in=["Diesel", "Gasoline", "Hybrid", "Electric"]
    ).delete()
    VehicleType.objects.filter(
        vehicle_type__in=["Sedan", "SUV", "Hatchback", "Coupe"]
    ).delete()

    # Delete models
    Model.objects.filter(
        model_name__in=["3 Series", "C-Class", "Avensis", "Golf 5"]
    ).delete()

    # Delete brands
    Brand.objects.filter(
        brand_name__in=["BMW", "Mercedes", "Toyota", "Volkswagen"]
    ).delete()


class Migration(migrations.Migration):
    """
    Django migration for seeding vehicle-related data.

    Depends on 0002_seed_initial_data because it requires existing
    locations (for PhysicalVehicle).
    """

    dependencies = [
        ("api", "0002_seed_initial_data"),
    ]

    operations = [
        migrations.RunPython(seed_vehicle_data, reverse_code=unseed_vehicle_data),
    ]
