# Generated by Django 5.0.6 on 2024-08-15 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0174_alter_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='fddbf7c757c947f7a357a2b2529ab5a9', max_length=50, unique=True),
        ),
    ]
