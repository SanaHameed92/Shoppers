# Generated by Django 5.0.6 on 2024-08-11 19:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0156_remove_order_coupon_alter_order_order_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='coupon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.coupon'),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='f39da5d741f341ee9bade7e686088c2c', max_length=50, unique=True),
        ),
    ]
