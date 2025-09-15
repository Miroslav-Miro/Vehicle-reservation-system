from django.db import migrations

def seed_initial_data(apps, schema_editor):
    Role = apps.get_model("api", "Role")
    Location = apps.get_model("api", "Location")
    ReservationStatus = apps.get_model("api", "ReservationStatus")

    # Seed roles
    roles = ["user", "manager", "admin"]
    for r in roles:
        Role.objects.get_or_create(role_name=r)

    # Seed locations with real addresses
    locations = [
        ("Varna", "Bul. Slivnitsa 45, Varna, Bulgaria"),
        ("Varna", "Knyaz Boris I Blvd 112, Varna, Bulgaria"),
        ("Sofia", "Vitosha Blvd 15, Sofia, Bulgaria"),
        ("Sofia", "Tsarigradsko Shose 223, Sofia, Bulgaria"),
        ("Sofia", "Maria Luiza Blvd 75, Sofia, Bulgaria"),
        ("Plovdiv", "Hristo Botev Blvd 30, Plovdiv, Bulgaria"),
        ("Plovdiv", "6th September Blvd 120, Plovdiv, Bulgaria"),
    ]
    for city, address in locations:
        Location.objects.get_or_create(location_name=city, address=address)

    # Seed reservation statuses
    statuses = ["active", "cancelled", "completed"]
    for s in statuses:
        ReservationStatus.objects.get_or_create(status=s)


def unseed_initial_data(apps, schema_editor):
    Role = apps.get_model("api", "Role")
    Location = apps.get_model("api", "Location")
    ReservationStatus = apps.get_model("api", "ReservationStatus")

    # Remove roles
    Role.objects.filter(role_name__in=["user", "manager", "admin"]).delete()

    # Remove locations
    Location.objects.filter(location_name__in=["Varna", "Sofia", "Plovdiv"]).delete()

    # Remove reservation statuses
    ReservationStatus.objects.filter(status__in=["active", "cancelled", "completed"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_initial_data, reverse_code=unseed_initial_data),
    ]

