# Generated by Django 5.0.6 on 2024-08-07 08:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0117_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='62849968d83347cd8e7d1d1d606ed5bf', max_length=50, unique=True),
        ),
    ]
