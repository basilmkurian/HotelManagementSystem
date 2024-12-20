# Generated by Django 5.1.2 on 2024-12-01 19:03

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hms_app', '0025_remove_review_rating_review_cleanliness_rating_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payrollrecord',
            name='base_pay',
        ),
        migrations.RemoveField(
            model_name='payrollrecord',
            name='bonus',
        ),
        migrations.RemoveField(
            model_name='payrollrecord',
            name='overtime_pay',
        ),
        migrations.RemoveField(
            model_name='staffprofile',
            name='department',
        ),
        migrations.RemoveField(
            model_name='staffprofile',
            name='emergency_contact',
        ),
        migrations.RemoveField(
            model_name='staffprofile',
            name='emergency_phone',
        ),
        migrations.RemoveField(
            model_name='staffprofile',
            name='shift_end',
        ),
        migrations.RemoveField(
            model_name='staffprofile',
            name='shift_start',
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='base_salary',
            field=models.DecimalField(decimal_places=2, default=100000, max_digits=10),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='joining_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='payrollrecord',
            name='staff',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hms_app.staffprofile'),
        ),
        migrations.AlterField(
            model_name='payrollrecord',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('PAID', 'Paid')], default='PENDING', max_length=20),
        ),
        migrations.AlterField(
            model_name='staffprofile',
            name='hourly_rate',
            field=models.DecimalField(decimal_places=2, default=100, max_digits=6),
        ),
    ]
