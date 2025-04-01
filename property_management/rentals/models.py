from django.db import models
from django.utils import timezone
from decimal import Decimal

class Property(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Unit(models.Model):
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=100)
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True)
    monthly_rent = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.property.name if self.property else 'No Property'})"

class Tenant(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name

    @property
    def outstanding_balance(self):
        total_charges = self.lease_set.aggregate(models.Sum('charges__amount'))['charges__amount__sum'] or Decimal('0.00')
        total_payments = self.lease_set.aggregate(models.Sum('payments__amount'))['payments__amount__sum'] or Decimal('0.00')
        return total_charges - total_payments


class Lease(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    outstanding_balance_age_days = models.IntegerField(default=0)

    def __str__(self):
        return f"Lease: {self.tenant.name} - {self.unit.name}"

    @property
    def is_active(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class Payment(models.Model):
    lease = models.ForeignKey(Lease, related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Payment of ${self.amount} on {self.date} for {self.lease}"


class Charge(models.Model):
    lease = models.ForeignKey(Lease, related_name='charges', on_delete=models.CASCADE)
    description = models.CharField(max_length=255, default='Monthly Rent')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    due_date = models.DateField()

    def __str__(self):
        return f"Charge of ${self.amount} on {self.due_date} for {self.lease}"


class Application(models.Model):
    applicant_name = models.CharField(max_length=100)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    submitted_on = models.DateTimeField(default=timezone.now)

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    def __str__(self):
        return f"{self.applicant_name} - {self.unit.name} ({self.get_status_display()})"