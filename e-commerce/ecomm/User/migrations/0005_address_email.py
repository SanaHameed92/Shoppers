# Generated by Django 5.0.6 on 2024-07-20 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User', '0004_address_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='email',
            field=models.EmailField(blank=True, max_length=255, null=True),
        ),
    ]
