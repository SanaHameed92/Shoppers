# Generated by Django 5.0.6 on 2024-08-02 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0056_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='649d42a2c93a4f5d903f86c5cabb11df', max_length=50, unique=True),
        ),
    ]
