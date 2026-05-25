from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Product, ProductCategory


BRAIDING_HAIR = {
    "name": "Braiding Hair",
    "slug": "braiding-hair",
    "description": "Premium braiding hair in a range of textures, lengths, and colors.",
}

HAIR_PRODUCTS = {
    "name": "Hair Products",
    "slug": "hair-products",
    "description": "Salon-grade styling, conditioning, and finishing products.",
}


BRAIDING_HAIR_ITEMS = [
    {
        "name": "Braiding Hair",
        "description": "High-quality braiding hair, soft and tangle-free. Available in multiple lengths and colors.",
        "price": 25000,
        "is_featured": True,
        "stock_quantity": 50,
    },
]


HAIR_PRODUCT_ITEMS = [
    {
        "name": "Braiding Gel",
        "description": "Long-hold braiding gel for sleek, frizz-free installs that last.",
        "price": 8000,
        "stock_quantity": 30,
    },
    {
        "name": "Hair Mousse (Braiding)",
        "description": "Lightweight braiding mousse — adds shine and tames flyaways without flaking.",
        "price": 12000,
        "stock_quantity": 25,
    },
    {
        "name": "Edge Control Gel",
        "description": "Strong-hold edge control for laying baby hairs and slicked-back styles.",
        "price": 7000,
        "stock_quantity": 40,
    },
    {
        "name": "Leave-In Conditioner",
        "description": "Daily leave-in conditioner that softens, detangles, and protects against breakage.",
        "price": 15000,
        "stock_quantity": 20,
    },
    {
        "name": "Hair Oil",
        "description": "Nourishing hair oil blend for shine, scalp health, and split-end protection.",
        "price": 10000,
        "stock_quantity": 35,
    },
    {
        "name": "Batana Oil Butter",
        "description": "Rich batana oil butter — deeply moisturizes and supports hair growth and strength.",
        "price": 25000,
        "is_featured": True,
        "stock_quantity": 15,
    },
    {
        "name": "Magic Curl Conditioner",
        "description": "Curl-defining conditioner that hydrates, reduces frizz, and brings curls back to life.",
        "price": 14000,
        "stock_quantity": 20,
    },
    {
        "name": "Lace Melting Spray",
        "description": "Lace melting spray for a flawless, undetectable wig install.",
        "price": 18000,
        "stock_quantity": 18,
    },
    {
        "name": "Oil Moisturizer",
        "description": "Daily oil moisturizer — locks in hydration and adds healthy shine.",
        "price": 12000,
        "stock_quantity": 25,
    },
]


class Command(BaseCommand):
    help = "Seed product categories and products (idempotent — safe to re-run)."

    @transaction.atomic
    def handle(self, *args, **options):
        braiding_cat, created = ProductCategory.objects.get_or_create(
            slug=BRAIDING_HAIR["slug"],
            defaults={
                "name": BRAIDING_HAIR["name"],
                "description": BRAIDING_HAIR["description"],
            },
        )
        self.stdout.write(
            f"{'+ created' if created else '= exists '} category: {braiding_cat.name}"
        )

        hair_products_cat, created = ProductCategory.objects.get_or_create(
            slug=HAIR_PRODUCTS["slug"],
            defaults={
                "name": HAIR_PRODUCTS["name"],
                "description": HAIR_PRODUCTS["description"],
            },
        )
        self.stdout.write(
            f"{'+ created' if created else '= exists '} category: {hair_products_cat.name}"
        )

        for item in BRAIDING_HAIR_ITEMS:
            self._upsert_product(item, braiding_cat)

        for item in HAIR_PRODUCT_ITEMS:
            self._upsert_product(item, hair_products_cat)

        self.stdout.write(self.style.SUCCESS("\nSeed complete."))

    def _upsert_product(self, item: dict, category: ProductCategory) -> None:
        defaults = {
            "name": item["name"],
            "description": item.get("description", ""),
            "price": item["price"],
            "category": category,
            "is_active": True,
            "is_featured": item.get("is_featured", False),
            "in_stock": True,
            "stock_quantity": item.get("stock_quantity", 10),
        }
        slug = item["name"].lower().replace("(", "").replace(")", "")
        slug = "-".join(slug.split())
        product, created = Product.objects.get_or_create(slug=slug, defaults=defaults)
        if not created:
            for field, value in defaults.items():
                setattr(product, field, value)
            product.save()
        self.stdout.write(
            f"  {'+ created' if created else '~ updated'} product: {product.name} "
            f"(TSh {int(product.price):,})"
        )
