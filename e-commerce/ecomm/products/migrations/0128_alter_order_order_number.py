# Generated by Django 5.0.6 on 2024-08-09 00:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0127_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='7e06d6a3e8e04318b51ea578a4742ce8', max_length=50, unique=True),
        ),
    ]
