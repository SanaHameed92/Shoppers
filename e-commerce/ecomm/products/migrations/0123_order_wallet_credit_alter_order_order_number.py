# Generated by Django 5.0.6 on 2024-08-08 06:59

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0122_alter_cart_user_alter_order_order_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='wallet_credit',
            field=models.DecimalField(blank=True, decimal_places=2, default=Decimal('0.00'), max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='5acf6da849dc4f459570a5f52dfa0da3', max_length=50, unique=True),
        ),
    ]
