# Generated by Django 5.0.6 on 2024-08-08 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0125_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='34e6195456a84cfaa0301de0273e38a7', max_length=50, unique=True),
        ),
    ]
