# Generated for VIP pricing and ServiceStyle multi-image carousel.

import cloudinary.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicestyle",
            name="vip_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Optional VIP-tier price for this same style. Surfaced in the VIP section.",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.CreateModel(
            name="ServiceStyleImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("image", cloudinary.models.CloudinaryField(max_length=255, verbose_name="image")),
                ("alt_text", models.CharField(blank=True, max_length=200)),
                ("is_primary", models.BooleanField(default=False)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                (
                    "style",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="api.servicestyle",
                    ),
                ),
            ],
            options={"ordering": ["sort_order"]},
        ),
    ]
