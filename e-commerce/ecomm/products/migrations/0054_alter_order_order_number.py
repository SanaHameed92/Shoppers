# Generated by Django 5.0.6 on 2024-08-02 01:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0053_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='32520b7dd28a416994c53dd94d20ca0a', max_length=50, unique=True),
        ),
    ]
