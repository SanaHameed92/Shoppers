# Generated by Django 5.0.6 on 2024-08-12 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0161_order_applied_coupon_code_order_discount_amount_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='applied_coupon_code',
        ),
        migrations.RemoveField(
            model_name='order',
            name='discount_amount',
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='a53166396f8a4195b8b6e23cf12806f0', max_length=50, unique=True),
        ),
    ]
