# Generated by Django 5.2 on 2025-05-21 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('otp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='phoneotp',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
    ]
