# Generated by Django 5.0.6 on 2024-08-03 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0072_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='f920be9e20a147ac80b16f3adfd1ad44', max_length=50, unique=True),
        ),
    ]
