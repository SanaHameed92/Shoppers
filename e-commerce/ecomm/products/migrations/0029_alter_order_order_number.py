# Generated by Django 5.0.6 on 2024-07-21 19:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0028_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='45ea31034c88447ba06edc7db6f73783', max_length=50, unique=True),
        ),
    ]
