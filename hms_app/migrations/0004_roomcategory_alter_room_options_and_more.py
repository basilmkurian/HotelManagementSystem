# Generated by Django 5.1.2 on 2024-11-26 17:21

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hms_app', '0003_alter_booking_options_remove_booking_is_checked_in_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoomCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'Room Categories',
            },
        ),
        migrations.AlterModelOptions(
            name='room',
            options={'ordering': ['room_number']},
        ),
        migrations.RemoveField(
            model_name='room',
            name='is_available',
        ),
        migrations.RemoveField(
            model_name='room',
            name='price_per_night',
        ),
        migrations.RemoveField(
            model_name='room',
            name='room_type',
        ),
        migrations.AddField(
            model_name='room',
            name='bed_count',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='room',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='room',
            name='has_ac',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='room',
            name='has_wifi',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='room',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='room_images/'),
        ),
        migrations.AddField(
            model_name='room',
            name='max_occupancy',
            field=models.PositiveIntegerField(default=2),
        ),
        migrations.AddField(
            model_name='room',
            name='status',
            field=models.CharField(choices=[('AVAILABLE', 'Available'), ('OCCUPIED', 'Occupied'), ('MAINTENANCE', 'Under Maintenance')], default='AVAILABLE', max_length=20),
        ),
        migrations.AddField(
            model_name='room',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='room',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='rooms', to='hms_app.roomcategory'),
        ),
    ]