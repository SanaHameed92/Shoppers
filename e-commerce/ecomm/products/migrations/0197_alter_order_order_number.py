# Generated by Django 5.0.6 on 2024-08-28 02:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0196_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='4ed1d91056504da8a73a0f95084288fa', max_length=50, unique=True),
        ),
    ]
