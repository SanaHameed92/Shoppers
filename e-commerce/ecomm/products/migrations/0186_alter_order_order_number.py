# Generated by Django 5.0.6 on 2024-08-23 01:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0185_alter_brand_brand_offer_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='746c6457bd0e4f35b2e63749cd956b2f', max_length=50, unique=True),
        ),
    ]
