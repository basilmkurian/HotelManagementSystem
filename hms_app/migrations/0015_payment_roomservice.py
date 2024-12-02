# Generated by Django 5.1.2 on 2024-11-29 11:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hms_app', '0014_remove_review_cleanliness_rating_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_method', models.CharField(choices=[('CASH', 'Cash'), ('CREDIT_CARD', 'Credit Card'), ('DEBIT_CARD', 'Debit Card'), ('UPI', 'UPI'), ('WALLET', 'Digital Wallet')], max_length=20)),
                ('transaction_id', models.CharField(blank=True, max_length=100)),
                ('payment_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default='SUCCESS', max_length=20)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hms_app.booking')),
            ],
        ),
        migrations.CreateModel(
            name='RoomService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_type', models.CharField(choices=[('FOOD', 'Food & Beverages'), ('LAUNDRY', 'Laundry'), ('HOUSEKEEPING', 'Housekeeping'), ('OTHER', 'Other Services')], max_length=20)),
                ('description', models.TextField()),
                ('cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=0.18, max_digits=4)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='room_services', to='hms_app.booking')),
            ],
        ),
    ]
