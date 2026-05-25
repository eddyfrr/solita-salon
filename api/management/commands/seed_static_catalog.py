"""Seed the static frontend catalog (src/data/products.ts) into the DB.

The shop UI reads products from a static TS file, but the checkout API
validates `product_slug` against the DB. Without this, every order
fails with Product.DoesNotExist.

Idempotent: safe to re-run after adding new products to the TS file.
"""

import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Product, ProductCategory


BRAIDING_HAIR_CATEGORY = {
    "slug": "braiding-hair",
    "name": "Braiding Hair",
    "description": "Premium braiding hair in a range of textures, lengths, and colors.",
}

USD_TO_TZS_FALLBACK = 2500  # used only if live FX is unavailable

PROJECT_ROOT = Path(settings.BASE_DIR).parent
PRODUCTS_TS = PROJECT_ROOT / "src" / "data" / "products.ts"


def _parse_lower_price_usd(price_str: str) -> Decimal | None:
    match = re.search(r"\$\s*(\d+(?:\.\d+)?)", price_str or "")
    return Decimal(match.group(1)) if match else None


def _load_products_via_node() -> list[dict]:
    """Use Node 22's native TS stripping to dump the static catalog as JSON."""
    result = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            "--input-type=module",
            "-e",
            "import {allProducts} from './src/data/products.ts'; "
            "console.log(JSON.stringify(allProducts));",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


class Command(BaseCommand):
    help = "Seed the static frontend product catalog into the DB (idempotent)."

    def handle(self, *args, **options):
        if not PRODUCTS_TS.exists():
            self.stderr.write(f"Static catalog not found: {PRODUCTS_TS}")
            return

        try:
            products = _load_products_via_node()
        except subprocess.CalledProcessError as exc:
            self.stderr.write(f"Failed to load TS catalog via node: {exc.stderr}")
            return

        category, created = ProductCategory.objects.get_or_create(
            slug=BRAIDING_HAIR_CATEGORY["slug"],
            defaults={
                "name": BRAIDING_HAIR_CATEGORY["name"],
                "description": BRAIDING_HAIR_CATEGORY["description"],
            },
        )
        self.stdout.write(
            f"{'+ created' if created else '= exists '} category: {category.name}"
        )

        rate = USD_TO_TZS_FALLBACK
        try:
            from api.payments import get_tzs_per_usd
            rate = get_tzs_per_usd()
            self.stdout.write(f"Using live TZS/USD rate: {rate:.2f}")
        except Exception:
            self.stdout.write(f"Using fallback TZS/USD rate: {rate}")

        created_count = updated_count = 0
        with transaction.atomic():
            for item in products:
                slug = item["slug"]
                name = item["title"].strip()
                usd_price = _parse_lower_price_usd(item.get("price", ""))
                tzs_price = (
                    int(usd_price * Decimal(rate)) if usd_price else 0
                )

                defaults = {
                    "name": name,
                    "description": item.get("description", "") or "",
                    "price": tzs_price,
                    "category": category,
                    "is_active": not item.get("isOutOfStock", False),
                    "in_stock": not item.get("isOutOfStock", False),
                    "stock_quantity": 20 if not item.get("isOutOfStock") else 0,
                }
                product, was_created = Product.objects.get_or_create(
                    slug=slug, defaults=defaults,
                )
                if was_created:
                    created_count += 1
                else:
                    for field, value in defaults.items():
                        setattr(product, field, value)
                    product.save()
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {created_count} created, {updated_count} updated, "
                f"{len(products)} total."
            )
        )
