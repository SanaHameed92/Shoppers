# Generated by Django 5.0.6 on 2024-08-05 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0109_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='62dac7d0124d4a14888038657538e93d', max_length=50, unique=True),
        ),
    ]
