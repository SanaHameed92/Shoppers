# Generated by Django 5.0.6 on 2024-08-08 06:59

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_remove_account_wallet_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='wallet',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
    ]
