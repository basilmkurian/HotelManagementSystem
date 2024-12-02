# Generated by Django 5.1.2 on 2024-11-26 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hms_app', '0002_alter_user_two_factor_code'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='booking',
            options={'ordering': ['-created_at']},
        ),
        migrations.RemoveField(
            model_name='booking',
            name='is_checked_in',
        ),
        migrations.AddField(
            model_name='booking',
            name='adults',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='booking',
            name='booking_source',
            field=models.CharField(choices=[('DIRECT', 'Direct'), ('ONLINE', 'Online')], default='DIRECT', max_length=20),
        ),
        migrations.AddField(
            model_name='booking',
            name='children',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='booking',
            name='total_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]