# Generated by Django 5.0.6 on 2024-08-05 18:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0107_remove_cartitem_product_variant_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='e9d9a6fc2219475ab097427e3abc6b44', max_length=50, unique=True),
        ),
    ]
