# Generated by Django 5.0.6 on 2024-08-06 00:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0115_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='46aa51c7a8394637ba22a6d4fad2b09f', max_length=50, unique=True),
        ),
    ]
