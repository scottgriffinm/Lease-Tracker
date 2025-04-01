from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Property, Tenant, Lease, Application

def dashboard(request):
    # 1. Outstanding balances (sum of Tenant.current_balance)
    outstanding_balances = Tenant.objects.filter(current_balance__gt=0)
    total_outstanding = sum([tenant.current_balance for tenant in outstanding_balances])

    # 2. Rental listings: vacant vs occupied
    # Vacant = Properties that have no tenant or active lease
    all_properties = Property.objects.all()
    leased_property_ids = Lease.objects.filter(end_date__gte=timezone.now()).values_list('property_id', flat=True)
    occupied_count = len(set(leased_property_ids))
    vacant_count = all_properties.count() - occupied_count

    # 3. Rental applications (just fetch the latest 5 for display)
    rental_applications = Application.objects.order_by('-submitted_on')[:5]

    # 4. Expiring leases (next 30 days)
    now = timezone.now().date()
    next_30_days = now + timedelta(days=30)
    expiring_leases = Lease.objects.filter(end_date__lte=next_30_days, end_date__gte=now)

    # 5. Tasks and recent activity (placeholder)
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