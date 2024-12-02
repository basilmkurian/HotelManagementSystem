# Generated by Django 5.1.2 on 2024-12-01 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hms_app', '0027_remove_staffprofile_base_salary_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffprofile',
            name='base_pay',
            field=models.DecimalField(decimal_places=2, default=10000, max_digits=10),
        ),
    ]
