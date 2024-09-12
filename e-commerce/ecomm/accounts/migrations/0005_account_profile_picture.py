# Generated by Django 5.0.6 on 2024-07-17 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_account_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='profile_picture',
            field=models.ImageField(blank=True, default='profile_pics/default.jpg', null=True, upload_to='profile_pics/'),
        ),
    ]
