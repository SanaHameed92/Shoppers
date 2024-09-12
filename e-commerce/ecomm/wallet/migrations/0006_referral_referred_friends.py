# Generated by Django 5.0.6 on 2024-08-09 07:20

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0005_referral'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='referral',
            name='referred_friends',
            field=models.ManyToManyField(blank=True, related_name='referred_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
