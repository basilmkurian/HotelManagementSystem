# Generated by Django 5.1.2 on 2024-11-28 08:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hms_app', '0007_review'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('booking_confirmation', 'Booking Confirmation'), ('booking_cancellation', 'Booking Cancellation'), ('low_inventory', 'Low Inventory Alert'), ('maintenance', 'Maintenance Alert'), ('check_in_reminder', 'Check-in Reminder'), ('check_out_reminder', 'Check-out Reminder'), ('promotional', 'Promotional Offer'), ('feedback_request', 'Feedback Request')], max_length=50)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('link', models.CharField(blank=True, max_length=200, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
