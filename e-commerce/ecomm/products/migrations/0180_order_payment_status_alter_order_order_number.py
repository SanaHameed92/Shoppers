# Generated by Django 5.0.6 on 2024-08-19 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0179_alter_order_order_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed'), ('Refunded', 'Refunded')], default='Pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='21100ab896e048bfbfe9441c56c6fee1', max_length=50, unique=True),
        ),
    ]
