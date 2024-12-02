# Generated by Django 5.1.2 on 2024-12-01 22:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hms_app', '0030_remove_roomservice_booking_remove_staffprofile_user_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayrollRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('hours_worked', models.DecimalField(decimal_places=2, max_digits=10)),
                ('shifts_completed', models.IntegerField()),
                ('base_pay', models.DecimalField(decimal_places=2, max_digits=10)),
                ('bonus', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_pay', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('PAID', 'Paid')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payroll_records', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
