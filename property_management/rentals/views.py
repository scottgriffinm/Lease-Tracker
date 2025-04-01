from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta, datetime
from collections import Counter
from .models import Property, Unit, Tenant, Lease, Application, Payment
import json

def dashboard(request):
    now = timezone.now()
    today = now.date()
    two_days_ago = now - timedelta(days=2)

    # Outstanding balances
    leases = Lease.objects.filter(outstanding_balance__gt=0).select_related('tenant', 'unit__property')
    outstanding_leases = list(leases)
    total_outstanding = sum(lease.outstanding_balance for lease in leases)

    # Rental listings: vacant vs occupied
    occupied_count = Unit.objects.filter(is_occupied=True).count()
    vacant_count = Unit.objects.filter(is_occupied=False).count()

    # Rental applications
    rental_applications = Application.objects.select_related('unit__property').order_by('-submitted_on')

    # Expiring leases (next 30 days)
    next_30_days = today + timedelta(days=30)
    expiring_leases = Lease.objects.filter(
        end_date__lte=next_30_days, end_date__gte=today
    ).select_related('tenant', 'unit__property')

    # Group expiring leases by date for chart
    expiring_distribution = Counter(lease.end_date.strftime("%Y-%m-%d") for lease in expiring_leases)
    expiring_distribution = dict(sorted(expiring_distribution.items()))

    # Tasks
    tasks = [
        {"title": "Fix Broken Screen", "due_date": "2025-04-05", "status": "In Progress"},
        {"title": "Paint Vacant Unit #101", "due_date": "2025-04-10", "status": "Not Started"},
    ]

    # Recent activity — strictly in the past 2 days
    recent_activity = []

    # Payments before now
    recent_payments = Payment.objects.filter(date__gte=two_days_ago.date(), date__lt=today).select_related('lease__tenant')
    for payment in recent_payments:
        payment_datetime = timezone.make_aware(datetime.combine(payment.date, datetime.min.time()))
        recent_activity.append({
            'timestamp': payment_datetime,
            'message': f"{payment.lease.tenant.name} paid ${int(payment.amount):,} towards rent"
        })

    # Applications submitted before now
    recent_apps = Application.objects.filter(submitted_on__gte=two_days_ago, submitted_on__lt=now).select_related('unit__property')
    for app in recent_apps:
        recent_activity.append({
            'timestamp': app.submitted_on,
            'message': f"Application from {app.applicant_name} for {app.unit.property.name} #{app.unit.number}"
        })

    # Lease expirations that already occurred (yesterday or day before)
    recent_expiring = Lease.objects.filter(end_date__lt=today, end_date__gte=today - timedelta(days=2)).select_related('tenant', 'unit__property')
    for lease in recent_expiring:
        lease_datetime = timezone.make_aware(datetime.combine(lease.end_date, datetime.min.time()))
        recent_activity.append({
            'timestamp': lease_datetime,
            'message': f"Lease for {lease.unit.property.name} #{lease.unit.number} (Tenant: {lease.tenant.name}) expired on {lease.end_date.strftime('%b %d')}."
        })

    # Sort and get the most recent 10 past events
    recent_activity = sorted(recent_activity, key=lambda x: x['timestamp'], reverse=True)[:10]
    recent_activity_messages = [
    {'message': entry['message'], 'timestamp': entry['timestamp']} for entry in recent_activity
    ]
    context = {
        'outstanding_balances': outstanding_leases,
        'total_outstanding': total_outstanding,
        'occupied_count': occupied_count,
        'vacant_count': vacant_count,
        'rental_applications': rental_applications,
        'expiring_leases': expiring_leases,
        'expiring_leases_distribution': json.dumps(expiring_distribution),
        'tasks': tasks,
        'recent_activity': recent_activity_messages,
    }

    return render(request, 'rentals/dashboard.html', context)