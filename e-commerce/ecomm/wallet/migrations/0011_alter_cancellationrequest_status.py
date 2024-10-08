# Generated by Django 5.0.6 on 2024-08-23 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0010_cancellationrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cancellationrequest',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Rejected', 'Rejected')], default='Pending', max_length=10),
        ),
    ]
