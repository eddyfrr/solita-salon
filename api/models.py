from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

try:
    from cloudinary.models import CloudinaryField
except ImportError:
    # Fallback if cloudinary isn't installed
    CloudinaryField = lambda *args, **kwargs: models.ImageField(
        upload_to="uploads/", blank=kwargs.get("blank", False), null=kwargs.get("null", False)
    )


# ──────────────────────────────────────────────
# Products
# ──────────────────────────────────────────────

class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text="Original price before discount"
    )
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="products"
    )
    image = CloudinaryField("image", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = CloudinaryField("image")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order}"


# ──────────────────────────────────────────────
# Services & Booking
# ──────────────────────────────────────────────

class Service(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = CloudinaryField("image", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ServiceStyle(models.Model):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="styles"
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    price_from = models.DecimalField(max_digits=10, decimal_places=2)
    vip_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text="Optional VIP-tier price for this same style. Surfaced in the VIP section.",
    )
    duration = models.CharField(max_length=50, help_text="e.g. '3-5 hours'")
    image = CloudinaryField("image", blank=True, null=True)
    lengths = models.JSONField(
        blank=True, default=list,
        help_text='e.g. ["Waist Length", "Mid-Back", "Hip Length"]'
    )
    colors = models.JSONField(
        blank=True, default=list,
        help_text='e.g. ["Black", "Brown", "Blonde"]'
    )
    types = models.JSONField(
        blank=True, default=list,
        help_text='e.g. ["Small", "Medium", "Large"]'
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]
        unique_together = ["service", "slug"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service.name} — {self.name}"


class ServiceStyleImage(models.Model):
    """Additional images for a service style — rendered as an Instagram-style carousel."""

    style = models.ForeignKey(
        ServiceStyle, on_delete=models.CASCADE, related_name="images"
    )
    image = CloudinaryField("image")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.style.name} — Image {self.sort_order}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        MPESA = "mpesa", "M-Pesa / Mobile Money"
        CARD = "card", "Card Payment"
        CASH = "cash", "Pay at Salon"

    # Client info (supports guest checkout)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="bookings"
    )
    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=30)
    notes = models.TextField(blank=True)

    # Service details
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    style = models.ForeignKey(ServiceStyle, on_delete=models.CASCADE)
    selected_length = models.CharField(max_length=100, blank=True)
    selected_color = models.CharField(max_length=100, blank=True)
    selected_type = models.CharField(max_length=100, blank=True)

    # Appointment
    date = models.DateField()
    time = models.TimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Status & payment
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH
    )
    is_paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.client_name} — {self.style.name} on {self.date} at {self.time}"


# ──────────────────────────────────────────────
# Orders (product purchases)
# ──────────────────────────────────────────────

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="orders"
    )
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30)
    shipping_address = models.TextField()

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} — {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


# ──────────────────────────────────────────────
# Gallery
# ──────────────────────────────────────────────

class GalleryPhoto(models.Model):
    image = CloudinaryField("image")
    caption = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Gallery Photo — {self.created_at.strftime('%Y-%m-%d')}"
