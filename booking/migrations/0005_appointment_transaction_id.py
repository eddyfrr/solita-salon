# Generated by Django 5.1.7 on 2025-05-01 08:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0004_rename_paid_appointment_is_paid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
