# Generated by Django 5.0.6 on 2024-08-09 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0134_offer_alter_order_order_number_brand_offer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='cffb4d3321984055a112b7a448f6f1ac', max_length=50, unique=True),
        ),
    ]
