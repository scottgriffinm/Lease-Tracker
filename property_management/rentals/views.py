from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Property, Unit, Tenant, Lease, Application

def dashboard(request):
    # 1. Outstanding balances (sum of Tenant.current_balance)
    outstanding_balances = Lease.objects.filter(
        tenant__current_balance__gt=0
    ).select_related('tenant', 'unit__property')
    total_outstanding = sum([lease.tenant.current_balance for lease in outstanding_balances])

    # 2. Rental listings: vacant vs occupied
    all_units = Unit.objects.select_related('property')
    active_leases = Lease.objects.filter(
        end_date__gte=timezone.now()
    ).values_list('unit_id', flat=True)

    occupied_count = all_units.filter(id__in=active_leases).count()
    vacant_count = all_units.exclude(id__in=active_leases).count()

    # 3. Rental applications (latest 5)
    rental_applications = Application.objects.select_related('unit__property').order_by('-submitted_on')[:5]

    # 4. Expiring leases (next 30 days)
    now = timezone.now().date()
    next_30_days = now + timedelta(days=30)
    expiring_leases = Lease.objects.filter(
        end_date__lte=next_30_days, end_date__gte=now
    ).select_related('tenant', 'unit__property')

    # 5. Placeholder tasks and recent activity
    tasks = [
        {"title": "Fix Broken Screen", "due_date": "2025-04-05", "status": "In Progress"},
        {"title": "Paint Vacant Unit #101", "due_date": "2025-04-10", "status": "Not Started"},
    ]
    recent_activity = [
        "Tenant John Smith paid $500 towards rent.",
        "Application from David Miller received.",
        "Lease renewal for Unit #202 approved."
    ]

    context = {
        'outstanding_balances': outstanding_balances,
        'total_outstanding': total_outstanding,
        'occupied_count': occupied_count,
        'vacant_count': vacant_count,
        'rental_applications': rental_applications,
        'expiring_leases': expiring_leases,
        'tasks': tasks,
        'recent_activity': recent_activity,
    }
    return render(request, 'rentals/dashboard.html', context)