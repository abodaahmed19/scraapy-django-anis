# Generated by Django 5.2 on 2025-05-26 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pms', '0004_alter_user_user_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='pickup_address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
