from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from collections import Counter
from .models import Property, Unit, Tenant, Lease, Application
import json

def dashboard(request):
    now = timezone.now().date()

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
    next_30_days = now + timedelta(days=30)
    expiring_leases = Lease.objects.filter(
        end_date__lte=next_30_days, end_date__gte=now
    ).select_related('tenant', 'unit__property')
    
    # Compute the distribution: group leases by end_date (formatted as YYYY-MM-DD)
    expiring_distribution = Counter(lease.end_date.strftime("%Y-%m-%d") for lease in expiring_leases)
    # Optionally sort the dictionary by date
    expiring_distribution = dict(sorted(expiring_distribution.items()))

    # Placeholder tasks and recent activity
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
        'expiring_leases_distribution': json.dumps(expiring_distribution),
        'tasks': tasks,
        'recent_activity': recent_activity,
    }
    return render(request, 'rentals/dashboard.html', context)