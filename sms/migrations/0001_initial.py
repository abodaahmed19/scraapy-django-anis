# Generated by Django 5.2 on 2025-05-26 13:16

import django.db.models.deletion
import sms.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BankingInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150)),
                ('bank_name', models.CharField(max_length=100)),
                ('iban_number', models.CharField(max_length=24)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ScrapItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('size', models.CharField(max_length=50)),
                ('quantity', models.PositiveIntegerField()),
                ('description', models.TextField(max_length=500)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('treated', 'Treated')], default='pending', max_length=10)),
                ('banking_info', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sms.bankinginfo')),
                ('category_group', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ScrapImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=sms.models.custom_asset_upload_path)),
                ('scrap_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='sms.scrapitem')),
            ],
        ),
    ]
