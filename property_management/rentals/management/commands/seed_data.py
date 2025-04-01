from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import timedelta
from rentals.models import Property, Unit, Tenant, Lease, Application

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds the database with fake rental data.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # Clear old data
        Application.objects.all().delete()
        Lease.objects.all().delete()
        Tenant.objects.all().delete()
        Unit.objects.all().delete()
        Property.objects.all().delete()

        # Create properties and units
        properties = []
        for _ in range(10):
            prop = Property.objects.create(
                name=random.choice([
                    "Maple Grove", "Oakview", "Cedar Flats", "Stonehill", "Pine Ridge",
                    "Heights", "Riverbend", "Lakeside", "Elm Court", "Brookside",
                    "Park Place", "Sunset Point", "Hilltop", "Reserve", "Skyline",
                    "Meadow Run", "Forest Glen", "Pines", "Westwood", "Creekside"
                ]),
                address=fake.address()
            )
            properties.append(prop)

            # Create 500 units for each property
            for i in range(1, 501):
                Unit.objects.create(
                    name=f"Unit {i}",
                    number=str(i),
                    property=prop,
                    monthly_rent=random.randint(800, 2500)
                )

        # Create tenants
        tenants = []
        available_units = list(Unit.objects.all())
        random.shuffle(available_units)

        for _ in range(150):  # Create 150 tenants
            unit = available_units.pop() if available_units else None
            if not unit:
                break

            tenant = Tenant.objects.create(
                name=fake.name(),
                email=fake.email(),
                phone=fake.phone_number(),
                current_balance=random.choice([0, 0, 0, 50, 100, 250, 500])
            )
            tenants.append((tenant, unit))

        # Create leases
        for tenant, unit in tenants:
            start = fake.date_between(start_date='-2y', end_date='today')
            end = start + timedelta(days=random.randint(180, 365))
            Lease.objects.create(
                tenant=tenant,
                unit=unit,
                start_date=start,
                end_date=end,
                monthly_rent=unit.monthly_rent
            )

        # Create rental applications
        for _ in range(30):
            unit = random.choice(Unit.objects.all())
            Application.objects.create(
                applicant_name=fake.name(),
                unit=unit,
                status=random.choice(['pending', 'approved', 'rejected']),
                submitted_on=fake.date_time_between(start_date='-30d', end_date='now')
            )

        self.stdout.write(self.style.SUCCESS("✅ Fake data seeded successfully!"))