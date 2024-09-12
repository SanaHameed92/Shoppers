# Generated by Django 5.0.6 on 2024-08-10 02:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0143_remove_product_discount_product_offer_price_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='offer_percentage',
        ),
        migrations.RemoveField(
            model_name='product',
            name='offer_price',
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='544a87f51e07462d86640d8c5b9272aa', max_length=50, unique=True),
        ),
    ]
