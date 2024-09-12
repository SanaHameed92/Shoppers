# Generated by Django 5.0.6 on 2024-08-15 01:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0169_orderitem_total_price_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='a9fc6d8d690a4cae94b3c1dbc381f9eb', max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='total_price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
