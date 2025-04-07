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
        property_names_used = set()
        possible_property_names = [
                    "Maple Grove", "Oakview", "Cedar Flats", "Stonehill", "Pine Ridge",
                    "Heights", "Riverbend", "Lakeside", "Elm Court", "Brookside",
                    "Park Place", "Sunset Point", "Hilltop", "Reserve", "Skyline",
                    "Meadow Run", "Forest Glen", "Pines", "Westwood", "Creekside"
                ]
        for _ in range(10):
            property_name = random.choice(possible_property_names)
            while property_name in property_names_used:
                property_name = random.choice(possible_property_names)
            property_names_used.add(property_name)
            prop = Property.objects.create(
                name=property_name,
                address=fake.address()
            )
            for i in range(1, 501):
                Unit.objects.create(
                    name=f"Unit {i}",
                    number=str(i),
                    property=prop,
                    monthly_rent=random.randint(800, 2500),
                    beds=random.randint(1, 5),
                    baths=random.randint(1, 3)
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
                name=" ".join(fake.name().split()[:3]),
                email=fake.email(),
                phone=fake.phone_number(),
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
                employment_status=True, 
                monthly_income=Decimal(random.randint(3000, 12000)), 
                background_check_passed=True, 
                emergency_contact_name=" ".join(fake.name().split()[:3]),
                emergency_contact_phone=fake.phone_number(),
                notes=""  
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

        # Create rental applications (for vacant units)
        vacant_units = list(Unit.objects.filter(is_occupied=False))
        random.shuffle(vacant_units)
        
        for unit in vacant_units:
            # Decide randomly: 25% no apps (stays Vacant), 30% review (Applications), 30% approved (Pending), 15% rejected only
            decision = random.choices(
                ['no_app', 'review', 'approved', 'rejected'],
                weights=[25, 30, 30, 15],
                k=1
            )[0]

            if decision == 'no_app':
                continue  # Leave as truly vacant

            num_apps = random.randint(1, 2) if decision != 'no_app' else 0
            statuses = []

            if decision == 'review':
                statuses = ['review'] * num_apps
            elif decision == 'approved':
                statuses = ['approved'] + ['review'] * (num_apps - 1)
            elif decision == 'rejected':
                statuses = ['rejected'] * num_apps

            for status in statuses:
                employment_status = random.choices([True, False], weights=[0.8, 0.2])[0]
                monthly_income = Decimal(random.randint(2500, 10000)) if employment_status else None
                background_check_passed = random.choices([True, False], weights=[0.9, 0.1])[0]
                
                applicant = Tenant.objects.create(
                    name=" ".join(fake.name().split()[:3]),
                    email=fake.email(),
                    phone=fake.phone_number(),
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
                    credit_score=random.randint(550, 800),
                    employment_status=employment_status,
                    monthly_income=monthly_income,
                    background_check_passed=background_check_passed,
                    emergency_contact_name=" ".join(fake.name().split()[:3]),
                    emergency_contact_phone=fake.phone_number(),
                    notes=""
                )

                Application.objects.create(
                    applicant=applicant,
                    unit=unit,
                    status=status,
                    submitted_on=fake.date_time_between(start_date='-30d', end_date='now')
                )

        self.stdout.write(self.style.SUCCESS("✅ Fake data seeded successfully."))