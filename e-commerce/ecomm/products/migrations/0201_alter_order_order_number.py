# Generated by Django 5.0.6 on 2024-09-13 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0200_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='a3ebe43e0f9f42e88d087141be1486c0', max_length=50, unique=True),
        ),
    ]
