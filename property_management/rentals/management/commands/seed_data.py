from django.core.management.base import BaseCommand
from faker import Faker
import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from rentals.models import Property, Unit, Tenant, Lease, Application, Charge, Payment

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds the database with fake rental data.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # Clear old data
        Application.objects.all().delete()
        Payment.objects.all().delete()
        Charge.objects.all().delete()
        Lease.objects.all().delete()
        Tenant.objects.all().delete()
        Unit.objects.all().delete()
        Property.objects.all().delete()

        # Create properties and units
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

            for i in range(1, 501):
                Unit.objects.create(
                    name=f"Unit {i}",
                    number=str(i),
                    property=prop,
                    monthly_rent=random.randint(800, 2500)
                )

        # Create tenants & assign units (77% occupancy)
        all_units = list(Unit.objects.all())
        random.shuffle(all_units)
        num_occupied_units = int(len(all_units) * 0.77)
        occupied_units = all_units[:num_occupied_units]
        vacant_units = all_units[num_occupied_units:]

        tenants = []
        for unit in occupied_units:
            tenant = Tenant.objects.create(
                name=fake.name(),
                email=fake.email(),
                phone=fake.phone_number(),
            )
            tenants.append((tenant, unit))

        # Pick ~2% of tenants as "problem tenants"
        total_tenants = len(tenants)
        num_problem_tenants = max(1, int(total_tenants * 0.02))
        problem_tenant_indexes = set(random.sample(range(total_tenants), num_problem_tenants))

        # Create leases and simulate charges + payments
        for i, (tenant, unit) in enumerate(tenants):
            start = fake.date_between(start_date='-1y', end_date='-90d')
            end = start + timedelta(days=365)
            lease = Lease.objects.create(
                tenant=tenant,
                unit=unit,
                start_date=start,
                end_date=end,
                monthly_rent=unit.monthly_rent
            )

            # Mark unit as occupied
            unit.is_occupied = True
            unit.save()

            today = timezone.now().date()
            current_date = start.replace(day=1)
            is_problem_tenant = i in problem_tenant_indexes
            missed_months = random.choice([1, 2]) if is_problem_tenant else 0

            charge_dates = []
            while current_date <= today and current_date <= end:
                charge_dates.append(current_date.replace(day=1))
                current_date += timedelta(days=32)
                current_date = current_date.replace(day=1)

            # Only consider unpaid charges with a due date in the past
            past_charge_dates = [d for d in charge_dates if d < today]
            unpaid_dates = set(past_charge_dates[-missed_months:]) if missed_months else set()

            total_charges = Decimal('0.00')
            total_payments = Decimal('0.00')

            for due_date in charge_dates:
                Charge.objects.create(
                    lease=lease,
                    description="Monthly Rent",
                    amount=lease.monthly_rent,
                    due_date=due_date
                )
                total_charges += lease.monthly_rent

                if due_date not in unpaid_dates:
                    Payment.objects.create(
                        lease=lease,
                        amount=lease.monthly_rent,
                        date=due_date - timedelta(days=1)
                    )
                    total_payments += lease.monthly_rent

            outstanding_balance = total_charges - total_payments
            lease.outstanding_balance = outstanding_balance

            # Compute age of oldest unpaid charge
            if unpaid_dates:
                oldest_unpaid_date = min(unpaid_dates)
                lease.outstanding_balance_age_days = (today - oldest_unpaid_date).days
            else:
                lease.outstanding_balance_age_days = 0

            lease.save()

        # Create rental applications
        vacant_units = list(Unit.objects.filter(is_occupied=False))

        for _ in range(300):
            if not vacant_units:
                break  # In case all units are occupied

            unit = random.choice(vacant_units)
            Application.objects.create(
                applicant_name=fake.name(),
                unit=unit,
                status=random.choice(['approved', 'rejected'] + ['pending'] * 10),
                submitted_on=fake.date_time_between(start_date='-30d', end_date='now')
            )

        self.stdout.write(self.style.SUCCESS("✅ Fake data seeded successfully with realistic occupancy and precomputed balances!"))