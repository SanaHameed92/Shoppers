# Generated by Django 5.0.6 on 2024-08-15 01:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0168_order_payment_status_alter_order_order_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='total_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='a5229cac4e0c4ecc9286292e4670e37f', max_length=50, unique=True),
        ),
    ]
