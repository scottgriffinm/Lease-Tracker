# Generated by Django 5.1.7 on 2025-04-01 03:13

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Lease',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('monthly_rent', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
            ],
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('address', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(blank=True, max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Charge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(default='Monthly Rent', max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('due_date', models.DateField()),
                ('lease', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='charges', to='rentals.lease')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('lease', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='rentals.lease')),
            ],
        ),
        migrations.AddField(
            model_name='lease',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rentals.tenant'),
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('number', models.CharField(max_length=100)),
                ('monthly_rent', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('property', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='rentals.property')),
            ],
        ),
        migrations.AddField(
            model_name='lease',
            name='unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rentals.unit'),
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('applicant_name', models.CharField(max_length=100)),
                ('submitted_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10)),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rentals.unit')),
            ],
        ),
    ]
