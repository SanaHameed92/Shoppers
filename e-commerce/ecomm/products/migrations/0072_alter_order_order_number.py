# Generated by Django 5.0.6 on 2024-08-03 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0071_alter_cartitem_added_at_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='c473b69c494a405ea5f664f57ea72d8b', max_length=50, unique=True),
        ),
    ]
