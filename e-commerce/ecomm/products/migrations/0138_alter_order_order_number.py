# Generated by Django 5.0.6 on 2024-08-09 23:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0137_brand_offer_percentage_category_offer_percentage_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='bc5d4495849c4ee097408dea77e34573', max_length=50, unique=True),
        ),
    ]
