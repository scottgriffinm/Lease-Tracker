from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Property, Unit, Tenant, Lease, Application

def dashboard(request):
    now = timezone.now().date()

    # 1. Outstanding balances (using updated field names)
    leases = Lease.objects.filter(outstanding_balance__gt=0).select_related('tenant', 'unit__property')
    outstanding_leases = list(leases)
    total_outstanding = sum(lease.outstanding_balance for lease in leases)

    # 2. Rental listings: vacant vs occupied (using precomputed flag)
    occupied_count = Unit.objects.filter(is_occupied=True).count()
    vacant_count = Unit.objects.filter(is_occupied=False).count()

    # 3. Rental applications (latest 5)
    rental_applications = Application.objects.select_related('unit__property').order_by('-submitted_on')[:5]

    # 4. Expiring leases (next 30 days)
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
        'outstanding_balances': outstanding_leases,
        'total_outstanding': total_outstanding,
        'occupied_count': occupied_count,
        'vacant_count': vacant_count,
        'rental_applications': rental_applications,
        'expiring_leases': expiring_leases,
        'tasks': tasks,
        'recent_activity': recent_activity,
    }
    return render(request, 'rentals/dashboard.html', context)