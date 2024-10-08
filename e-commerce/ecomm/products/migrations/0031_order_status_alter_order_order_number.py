# Generated by Django 5.0.6 on 2024-07-22 02:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0030_rename_price_orderitem_total_price_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled')], default='Pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='840cd4e802c34ca0b515ccc8b88aa417', max_length=50, unique=True),
        ),
    ]
