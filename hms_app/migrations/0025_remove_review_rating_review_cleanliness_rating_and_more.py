# Generated by Django 5.1.2 on 2024-12-01 13:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hms_app', '0024_alter_booking_advance_payment_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='review',
            name='rating',
        ),
        migrations.AddField(
            model_name='review',
            name='cleanliness_rating',
            field=models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=3, help_text='Rate cleanliness from 1-5'),
        ),
        migrations.AddField(
            model_name='review',
            name='food_rating',
            field=models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=3, help_text='Rate food quality from 1-5'),
        ),
        migrations.AddField(
            model_name='review',
            name='overall_rating',
            field=models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=3, help_text='Overall rating from 1-5'),
        ),
        migrations.AddField(
            model_name='review',
            name='staff_rating',
            field=models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=3, help_text='Rate staff behavior from 1-5'),
        ),
        migrations.AlterField(
            model_name='review',
            name='booking',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hms_app.booking'),
        ),
        migrations.AlterField(
            model_name='review',
            name='feedback',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='review',
            name='guest',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
