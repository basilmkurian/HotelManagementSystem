# Generated by Django 5.1.2 on 2024-11-30 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hms_app', '0018_alter_inventoryitem_category_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryitem',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
