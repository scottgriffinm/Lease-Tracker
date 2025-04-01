from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import timedelta, date
from rentals.models import Property, Tenant, Lease, Application

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds the database with fake rental data.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # Clear old data
        Application.objects.all().delete()
        Lease.objects.all().delete()
        Tenant.objects.all().delete()
        Property.objects.all().delete()

        # Create properties
        properties = []
        for _ in range(10):
            prop = Property.objects.create(
                name=random.choice(["Maple Grove", "Oakview", "Cedar Flats", "Stonehill", "Pine Ridge", "Heights", "Riverbend", "Lakeside", "Elm Court", "Brookside", "Park Place", "Sunset Point", "Hilltop", "Reserve", "Skyline", "Meadow Run", "Forest Glen", "Pines", "Westwood", "Creekside"]),
                address=fake.address(),
                monthly_rent=random.randint(800, 2500)
            )
            properties.append(prop)

        # Create tenants
        tenants = []
        for _ in range(15):
            prop = random.choice(properties)
            balance = random.choice([0, 0, 0, 50, 100, 250, 500])
            unit = str(random.randint(1, 500)) + random.choice(['a','b','c'] + [''] * 10)
            tenant = Tenant.objects.create(
                name=fake.name(),
                email=fake.email(),
                phone=fake.phone_number(),
                property=prop,
                unit=unit,
                current_balance=balance
            )
            tenants.append(tenant)

        # Create leases
        for tenant in tenants:
            if tenant.property:
                start = fake.date_between(start_date='-2y', end_date='today')
                end = start + timedelta(days=random.randint(180, 365))
                Lease.objects.create(
                    tenant=tenant,
                    property=tenant.property,
                    start_date=start,
                    end_date=end,
                    monthly_rent=tenant.property.monthly_rent
                )

        # Create rental applications
        for _ in range(10):
            Application.objects.create(
                applicant_name=fake.name(),
                property=random.choice(properties),
                unit=str(random.randint(1, 500)) + random.choice(['a','b','c'] + [''] * 10),
                status=random.choice(['pending', 'approved', 'rejected']),
                submitted_on=fake.date_time_between(start_date='-30d', end_date='now')
            )

        self.stdout.write(self.style.SUCCESS("✅ Fake data seeded successfully!"))