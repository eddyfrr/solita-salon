# Generated by Django 5.1.7 on 2025-06-05 14:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0006_alter_service_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='service',
            name='price',
        ),
        migrations.CreateModel(
            name='ServiceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_name', models.CharField(max_length=50)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='types', to='booking.service')),
            ],
        ),
        migrations.AddField(
            model_name='appointment',
            name='service_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='booking.servicetype'),
        ),
    ]
