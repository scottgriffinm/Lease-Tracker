from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.core.serializers import serialize
from datetime import timedelta, datetime
from collections import Counter
from .models import Property, Unit, Tenant, Lease, Application, Payment
from django.db.models import Prefetch
import json

# Get dashboard data
def dashboard(request):
    now = timezone.now()
    today = now.date()
    two_days_ago = now - timedelta(days=2)

    # Outstanding balances
    leases = Lease.objects.filter(outstanding_balance__gt=0).select_related('tenant', 'unit__property')
    outstanding_leases = list(leases)
    total_outstanding = sum(lease.outstanding_balance for lease in leases)

    # Occupied/Vacant/Pending Units
    occupied_count = Unit.objects.filter(is_occupied=True).count()
    vacant_units = Unit.objects.filter(is_occupied=False)
    pending_units = Application.objects.filter(status='pending').values_list('unit_id', flat=True)
    vacant_with_apps_count = vacant_units.filter(id__in=pending_units).count()
    vacant_no_apps_count = vacant_units.exclude(id__in=pending_units).count()

    # Rental applications
    rental_applications = Application.objects.select_related('unit__property').order_by('-submitted_on')
    pending_app_count = Application.objects.filter(status='pending').count()

    # Expiring leases (next 30 days)
    next_30_days = today + timedelta(days=30)
    expiring_leases = Lease.objects.filter(
        end_date__lte=next_30_days, end_date__gte=today
    ).select_related('tenant', 'unit__property')
    expiring_distribution = Counter(lease.end_date.strftime("%Y-%m-%d") for lease in expiring_leases) # Group by date
    expiring_distribution = dict(sorted(expiring_distribution.items()))

    # Tasks
    tasks = [
        {"title": "Fix Broken Screen", "due_date": "2025-04-05", "status": "In Progress"},
        {"title": "Paint Vacant Unit #101", "due_date": "2025-04-10", "status": "Not Started"},
    ]

    # Recent activity (past two days)
    recent_activity = []

    # Recent Payments
    recent_payments = Payment.objects.filter(date__gte=two_days_ago.date(), date__lt=today).select_related('lease__tenant')
    for payment in recent_payments:
        payment_datetime = timezone.make_aware(datetime.combine(payment.date, datetime.min.time()))
        recent_activity.append({
            'timestamp': payment_datetime,
            'message': f"{payment.lease.tenant.name} paid ${int(payment.amount):,} towards rent"
        })

    # Recent Applications
    recent_apps = Application.objects.filter(submitted_on__gte=two_days_ago, submitted_on__lt=now).select_related('unit__property')
    for app in recent_apps:
        recent_activity.append({
            'timestamp': app.submitted_on,
            'message': f"Application from {app.applicant_name} for {app.unit.property.name} #{app.unit.number}"
        })

    # Recent Lease expirations
    recent_expiring = Lease.objects.filter(end_date__lt=today, end_date__gte=today - timedelta(days=2)).select_related('tenant', 'unit__property')
    for lease in recent_expiring:
        lease_datetime = timezone.make_aware(datetime.combine(lease.end_date, datetime.min.time()))
        recent_activity.append({
            'timestamp': lease_datetime,
            'message': f"Lease for {lease.unit.property.name} #{lease.unit.number} (Tenant: {lease.tenant.name}) expired on {lease.end_date.strftime('%b %d')}."
        })

    # Get most recent 10 events
    recent_activity = sorted(recent_activity, key=lambda x: x['timestamp'], reverse=True)[:10]
    recent_activity_messages = [
        {'message': entry['message'], 'timestamp': entry['timestamp']} for entry in recent_activity
    ]

    # All units
    all_units = Unit.objects.select_related('property').prefetch_related(
        Prefetch('lease_set', queryset=Lease.objects.filter(end_date__gte=today).select_related('tenant'))
    )

    # Label Occupied/Pending/Vacant in all units set
    pending_unit_ids = set(pending_units)
    for unit in all_units:
        if unit.is_occupied:
            unit.status = "Occupied"
        elif unit.id in pending_unit_ids:
            unit.status = "Pending"
        else:
            unit.status = "Vacant"
        # Tenant for each unit
        active_lease = next(iter(unit.lease_set.all()), None)
        unit.tenant_name = active_lease.tenant.name if active_lease and active_lease.tenant else "None"

    # Build context
    context = {
        'outstanding_balances': outstanding_leases,
        'total_outstanding': total_outstanding,
        'occupied_count': occupied_count,
        'vacant_with_apps_count': vacant_with_apps_count,
        'vacant_no_apps_count': vacant_no_apps_count,
        'rental_applications': rental_applications,
        'pending_app_count': pending_app_count,
        'expiring_leases': expiring_leases,
        'expiring_leases_distribution': json.dumps(expiring_distribution),
        'tasks': tasks,
        'recent_activity': recent_activity_messages,
        'all_units': all_units,
        'today': today,
    }

    return render(request, 'rentals/dashboard.html', context)

# Get all units data
def units_api(request):
    units = Unit.objects.select_related('property').prefetch_related(
        Prefetch('lease_set', queryset=Lease.objects.filter(end_date__gte=timezone.now().date()).select_related('tenant'))
    )

    unit_data = []
    for unit in units:
        active_lease = next(iter(unit.lease_set.all()), None)
        tenant_name = active_lease.tenant.name if active_lease and active_lease.tenant else "None"

        if unit.is_occupied:
            status = "Occupied"
        elif Application.objects.filter(unit=unit, status='pending').exists():
            status = "Pending"
        else:
            status = "Vacant"

        unit_data.append({
            'property': unit.property.name,
            'unit': f'<a href="/units/{unit.id}/">#{unit.number}</a>',
            'address': unit.property.address,
            'tenant': tenant_name,
            'rent': f"${int(unit.monthly_rent):,}",
            'status': status
        })

    return JsonResponse({'data': unit_data})

# Get all people data
def people(request):
    tenants = Tenant.objects.prefetch_related(
        Prefetch('lease_set', queryset=Lease.objects.select_related('unit__property').prefetch_related('payments', 'charges'))
    )
    context = {
        'tenants': tenants
    }
    return render(request, 'rentals/people.html', context)

# Get one person's data
def person_detail(request, tenant_id):
    tenant = get_object_or_404(
        Tenant.objects.prefetch_related(
            Prefetch('lease_set', queryset=Lease.objects.select_related('unit__property').prefetch_related('payments', 'charges'))
        ),
        pk=tenant_id
    )

    # Prepare ledger for each lease
    for lease in tenant.lease_set.all():
        transactions = []

        for charge in lease.charges.all():
            transactions.append({
                'type': 'Charge',
                'amount': charge.amount,
                'date': charge.due_date,
                'description': charge.description or '',
            })

        for payment in lease.payments.all():
            transactions.append({
                'type': 'Payment',
                'amount': payment.amount,
                'date': payment.date,
                'description': f'Payment received',
            })

        # Sort by date descending (most recent first)
        lease.ledger = sorted(transactions, key=lambda x: x['date'], reverse=True)

    context = {
        'tenant': tenant
    }
    return render(request, 'rentals/person_detail.html', context)

# Get one unit's data
def unit_detail(request, unit_id):
    unit = get_object_or_404(
        Unit.objects.select_related('property').prefetch_related(
            Prefetch(
                'lease_set',
                queryset=Lease.objects.select_related('tenant').prefetch_related('payments', 'charges')
            )
        ),
        pk=unit_id
    )

    # Optionally build ledgers for each lease
    for lease in unit.lease_set.all():
        transactions = list(lease.charges.all()) + list(lease.payments.all())
        transactions.sort(key=lambda x: x.date if hasattr(x, 'date') else x.due_date, reverse=True)
        lease.ledger = [
            {
                'date': getattr(t, 'date', getattr(t, 'due_date', None)),
                'type': 'Payment' if hasattr(t, 'amount') and hasattr(t, 'lease') and hasattr(t, 'date') else 'Charge',
                'amount': t.amount,
                'description': getattr(t, 'description', 'Payment')
            }
            for t in transactions
        ]

    context = {
        'unit': unit
    }
    return render(request, 'rentals/unit_detail.html', context)

