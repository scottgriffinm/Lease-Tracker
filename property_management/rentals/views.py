from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import JsonResponse
from django.core.serializers import serialize
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta, datetime
from collections import Counter
from .models import Property, Unit, Tenant, Lease, Application, Payment, Task
from .forms import TaskForm
from django.db.models import Prefetch
import json

# GET View — `/`
def dashboard(request):
    now = timezone.now()
    today = now.date()
    two_days_ago = now - timedelta(days=2)

    # Outstanding balances
    leases = Lease.objects.filter(outstanding_balance__gt=0).select_related('tenant', 'unit__property')
    outstanding_leases = list(leases)
    total_outstanding = sum(lease.outstanding_balance for lease in leases)

    # Rental applications
    rental_applications = Application.objects.select_related('unit__property').order_by('-submitted_on')
    review_app_count = Application.objects.filter(status='review').count()

    # Expiring leases (next 30 days)
    next_30_days = today + timedelta(days=30)
    expiring_leases = Lease.objects.filter(
        end_date__lte=next_30_days, end_date__gte=today
    ).select_related('tenant', 'unit__property')
    expiring_distribution = Counter(lease.end_date.strftime("%Y-%m-%d") for lease in expiring_leases)
    expiring_distribution = dict(sorted(expiring_distribution.items()))

    # Tasks - Top 10 that are not completed
    tasks = Task.objects.exclude(status=Task.STATUS_COMPLETED).order_by('due_date')[:10]

    # Recent activity (past two days)
    recent_activity = []

    recent_payments = Payment.objects.filter(date__gte=two_days_ago.date(), date__lt=today).select_related('lease__tenant')
    for payment in recent_payments:
        payment_datetime = timezone.make_aware(datetime.combine(payment.date, datetime.min.time()))
        recent_activity.append({
            'timestamp': payment_datetime,
            'message': f"{payment.lease.tenant.name} paid ${int(payment.amount):,} towards rent"
        })

    recent_apps = Application.objects.filter(submitted_on__gte=two_days_ago, submitted_on__lt=now).select_related('unit__property')
    for app in recent_apps:
        recent_activity.append({
            'timestamp': app.submitted_on,
            'message': f"Application from {app.applicant.name} for {app.unit.property.name} #{app.unit.number}"
        })

    recent_expiring = Lease.objects.filter(end_date__lt=today, end_date__gte=today - timedelta(days=2)).select_related('tenant', 'unit__property')
    for lease in recent_expiring:
        lease_datetime = timezone.make_aware(datetime.combine(lease.end_date, datetime.min.time()))
        recent_activity.append({
            'timestamp': lease_datetime,
            'message': f"Lease for {lease.unit.property.name} #{lease.unit.number} (Tenant: {lease.tenant.name}) expired on {lease.end_date.strftime('%b %d')}."
        })

    recent_activity = sorted(recent_activity, key=lambda x: x['timestamp'], reverse=True)[:10]
    recent_activity_messages = [
        {'message': entry['message'], 'timestamp': entry['timestamp']} for entry in recent_activity
    ]

    # All units and status calculation
    all_units = Unit.objects.select_related('property').prefetch_related(
        Prefetch('lease_set', queryset=Lease.objects.filter(end_date__gte=today).select_related('tenant'))
    )

    approved_unit_ids = set(Application.objects.filter(status='approved').values_list('unit_id', flat=True))
    review_unit_ids = set(Application.objects.filter(status='review').values_list('unit_id', flat=True))

    occupied_count = 0
    pending_units_count = 0
    applications_count = 0
    vacant_units_count = 0

    for unit in all_units:
        if unit.is_occupied:
            unit.status = "Occupied"
            occupied_count += 1
        elif unit.id in approved_unit_ids:
            unit.status = "Pending"
            pending_units_count += 1
        elif unit.id in review_unit_ids:
            unit.status = "Applications"
            applications_count += 1
        else:
            unit.status = "Vacant"
            vacant_units_count += 1

        # Set tenant name if available
        active_lease = next(iter(unit.lease_set.all()), None)
        unit.tenant_name = active_lease.tenant.name if active_lease and active_lease.tenant else "None"

    # Context for template
    context = {
        'outstanding_balances': outstanding_leases,
        'total_outstanding': total_outstanding,
        'occupied_count': occupied_count,
        'pending_units_count': pending_units_count,
        'applications_count': applications_count,
        'vacant_no_apps_count': vacant_units_count,
        'rental_applications': rental_applications,
        'review_app_count': review_app_count,
        'expiring_leases': expiring_leases,
        'expiring_leases_distribution': json.dumps(expiring_distribution),
        'tasks': tasks,
        'recent_activity': recent_activity_messages,
        'all_units': all_units,
        'today': today,
    }

    return render(request, 'rentals/dashboard.html', context)

# GET API — `/api/units/`
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
        elif Application.objects.filter(unit=unit, status='approved').exists():
            status = "Pending"
        elif Application.objects.filter(unit=unit, status='review').exists():
            status = "Applications"
        else:
            status = "Vacant"

        unit_data.append({
            'property': f'<a href="/units/{unit.id}/">{unit.property.name}</a>',
            'unit': f'<a href="/units/{unit.id}/">#{unit.number}</a>',
            'address': f'<a href="/units/{unit.id}/">{unit.property.address}</a>',
            'tenant': tenant_name if tenant_name == "None" else f'<a href="/people/{active_lease.tenant.id}/">{tenant_name}</a>',
            'rent': f"${int(unit.monthly_rent):,}",
            'beds': f"{int(unit.beds):,}",
            'baths': f"{int(unit.baths):,}",
            'status': status
        })

    return JsonResponse({'data': unit_data})

# GET API — `/api/tenants/`
def tenants_api(request):
    tenants = Tenant.objects.prefetch_related(
        Prefetch('lease_set', queryset=Lease.objects.select_related('unit__property'))
    )

    tenant_data = []
    for tenant in tenants:
        if tenant.lease_set.exists():
            for lease in tenant.lease_set.all():
                tenant_data.append({
                    'name': f'<a href="/people/{tenant.id}/">{tenant.name}</a>',
                    'email': tenant.email,
                    'phone': tenant.phone,
                    'unit': f'<a href="/units/{lease.unit.id}/">{lease.unit.property.name} #{lease.unit.number}</a>',
                    'lease_dates': f'{lease.start_date} to {lease.end_date}',
                    'rent': f"${int(lease.monthly_rent):,}",
                    'outstanding': f"${lease.outstanding_balance:,.2f}" + (
                        f" ({lease.outstanding_balance_age_days}d)" if lease.outstanding_balance_age_days else ""
                    ),
                })
        else:
            tenant_data.append({
                'name': f'<a href="/people/{tenant.id}/">{tenant.name}</a>',
                'email': tenant.email,
                'phone': tenant.phone,
                'unit': '—',
                'lease_dates': '—',
                'rent': '—',
                'outstanding': f"${tenant.outstanding_balance:,.2f}",
            })

    return JsonResponse({'data': tenant_data})

# GET API — `/api/applications/`
def applications_api(request):
    apps = Application.objects.select_related('applicant', 'unit__property')
    data = []
    for app in apps:
        data.append({
            'id': app.id,
            'name': app.applicant.name,
            'email': app.applicant.email,
            'phone': app.applicant.phone,
            'unit': f"{app.unit.property.name} #{app.unit.number}",
            'submitted_on': app.submitted_on.strftime('%Y-%m-%d'),
            'status': app.status,
        })
    return JsonResponse({'data': data})

# GET View — `/people/`
def people(request):
    tenants = Tenant.objects.prefetch_related(
        Prefetch('lease_set', queryset=Lease.objects.select_related('unit__property').prefetch_related('payments', 'charges'))
    )
    context = {
        'tenants': tenants
    }
    return render(request, 'rentals/people.html', context)

# GET View — `/properties/`
def properties(request):
    return render(request, 'rentals/properties.html')

# GET View — `/applications/`
def applications(request):
    return render(request, 'rentals/applications.html')

# GET View — `/tasks/`
def tasks(request):
    tasks = Task.objects.select_related('property', 'unit').order_by('due_date')
    return render(request, 'rentals/tasks.html', {'tasks': tasks})

# GET View — `/people/<tenant_id>/`
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

# GET View — `/units/<unit_id>/`
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

    # Build ledgers for each lease
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

    # Collect any open applications
    applications = Application.objects.filter(unit=unit).order_by('-submitted_on')

    context = {
        'unit': unit,
        'applications': applications
    }

    return render(request, 'rentals/unit_detail.html', context)

# GET View — `/applications/<application_id>/`
def application_detail(request, application_id):
    app = get_object_or_404(Application.objects.select_related('unit__property', 'applicant'), pk=application_id)

    # Get all in review application IDs sorted by submission time
    review_apps = list(Application.objects.filter(status='review').order_by('submitted_on').values_list('id', flat=True))
    current_index = review_apps.index(app.id) if app.id in review_apps else -1
    prev_id = review_apps[current_index - 1] if current_index > 0 else None
    next_id = review_apps[current_index + 1] if current_index < len(review_apps) - 1 else None

    # Get other review applications for the same unit
    unit_review_apps = (
        Application.objects
        .filter(unit=app.unit, status='review')
        .select_related('applicant')
        .order_by('submitted_on')
    )

    return render(request, 'rentals/application_detail.html', {
        'application': app,
        'prev_app_id': prev_id,
        'next_app_id': next_id,
        'unit_review_apps': unit_review_apps 
    })

# GET View — `/tasks/<task_id>/`
def task_detail(request, task_id):
    task = get_object_or_404(Task.objects.select_related('property', 'unit'), pk=task_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Task.STATUS_CHOICES).keys():
            task.status = new_status
            task.save()
    return render(request, 'rentals/task_detail.html', {'task': task})

# GET API — `/api/units_by_property/`
def units_by_property(request):
    property_id = request.GET.get('property_id')
    units = Unit.objects.filter(property_id=property_id).order_by('number')
    unit_options = [{'id': u.id, 'text': f'Unit {u.number}'} for u in units]
    return JsonResponse({'units': unit_options})

# POST API — `/applications/<application_id>/update_status/`
@require_POST
def update_application_status(request, application_id):
    app = get_object_or_404(Application.objects.select_related('unit__property', 'applicant'), pk=application_id)
    new_status = request.POST.get('status')
    if new_status in [Application.STATUS_APPROVED, Application.STATUS_REJECTED]:
        app.status = new_status
        app.save()
        return JsonResponse({'success': True, 'new_status': app.get_status_display()})
    return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

# GET/POST API — `tasks/new/`
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tasks')  # Make sure this name matches your URL pattern
    else:
        form = TaskForm()

    return render(request, 'rentals/task_form.html', {'form': form})