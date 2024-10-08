# Generated by Django 5.0.6 on 2024-08-04 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0092_order_payment_id_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='e834e90e69974cbcba483d6df9ace55e', max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='quantity',
            field=models.PositiveIntegerField(),
        ),
    ]
