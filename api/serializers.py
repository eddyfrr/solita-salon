from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    ProductCategory, Product, ProductImage,
    Service, ServiceStyle, ServiceStyleImage,
    Booking, Order, OrderItem, GalleryPhoto,
)


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# ──────────────────────────────────────────────
# Products
# ──────────────────────────────────────────────

class ProductCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source="products.count", read_only=True)

    class Meta:
        model = ProductCategory
        fields = ["id", "name", "slug", "description", "product_count"]


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    # The model uses CloudinaryField; expose `image` as write-only so the
    # admin's multipart POST actually reaches Cloudinary.
    image = serializers.ImageField(write_only=True, required=True)

    class Meta:
        model = ProductImage
        fields = ["id", "image", "image_url", "alt_text", "is_primary", "sort_order"]

    def get_image_url(self, obj):
        if obj.image and getattr(obj.image, "url", None):
            return obj.image.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(),
        source="category", write_only=True, required=False, allow_null=True,
    )
    images = ProductImageSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "price", "compare_at_price",
            "category", "category_id", "image", "image_url", "images",
            "is_active", "is_featured", "in_stock", "stock_quantity",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "price", "compare_at_price",
            "category", "image", "is_active", "is_featured", "in_stock",
            "stock_quantity",
        ]


# ──────────────────────────────────────────────
# Services
# ──────────────────────────────────────────────

class ServiceStyleImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    # The model uses CloudinaryField; expose `image` as write-only so the
    # admin's multipart POST actually reaches Cloudinary.
    image = serializers.ImageField(write_only=True, required=True)

    class Meta:
        model = ServiceStyleImage
        fields = ["id", "image", "image_url", "alt_text", "is_primary", "sort_order"]

    def get_image_url(self, obj):
        if obj.image and getattr(obj.image, "url", None):
            return obj.image.url
        return None


class ServiceStyleSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    images = ServiceStyleImageSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceStyle
        fields = [
            "id", "name", "slug", "description", "price_from", "vip_price",
            "duration", "image", "image_url", "images",
            "lengths", "colors", "types",
            "is_active", "sort_order",
        ]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class ServiceSerializer(serializers.ModelSerializer):
    styles = ServiceStyleSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    style_count = serializers.IntegerField(source="styles.count", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id", "name", "slug", "description", "image", "image_url",
            "styles", "style_count", "is_active", "sort_order",
        ]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class ServiceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id", "name", "slug", "description", "image",
            "is_active", "sort_order",
        ]


class ServiceStyleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceStyle
        fields = [
            "id", "service", "name", "slug", "description", "price_from",
            "vip_price", "duration", "image", "lengths", "colors", "types",
            "is_active", "sort_order",
        ]
        read_only_fields = ["service"]


# ──────────────────────────────────────────────
# Bookings
# ──────────────────────────────────────────────

class BookingSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    style_name = serializers.CharField(source="style.name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "client_name", "client_email", "client_phone", "notes",
            "service", "service_name", "style", "style_name",
            "selected_length", "selected_color", "selected_type",
            "date", "time", "price",
            "status", "payment_method", "is_paid", "transaction_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


from datetime import time as _time
from django.db.models import Q

# Solita appointment slots — 4 fixed times per day.
ALLOWED_BOOKING_TIMES = (
    _time(6, 30),
    _time(8, 30),
    _time(10, 30),
    _time(14, 0),
)
MAX_BOOKINGS_PER_DAY = 16
ACTIVE_BOOKING_STATUSES = (
    Booking.Status.PENDING,
    Booking.Status.CONFIRMED,
    Booking.Status.COMPLETED,
)


def active_bookings_for_date(date):
    return Booking.objects.filter(date=date, status__in=ACTIVE_BOOKING_STATUSES)


class BookingCreateSerializer(serializers.Serializer):
    """Accepts slugs from the frontend and resolves to IDs."""
    client_name = serializers.CharField(max_length=200)
    client_email = serializers.EmailField()
    client_phone = serializers.CharField(max_length=30)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    service_slug = serializers.SlugField()
    style_slug = serializers.SlugField()
    selected_length = serializers.CharField(required=False, allow_blank=True, default="")
    selected_color = serializers.CharField(required=False, allow_blank=True, default="")
    selected_type = serializers.CharField(required=False, allow_blank=True, default="")
    date = serializers.DateField()
    time = serializers.TimeField()
    payment_method = serializers.ChoiceField(
        choices=Booking.PaymentMethod.choices, default="cash"
    )

    def validate_time(self, value):
        if value not in ALLOWED_BOOKING_TIMES:
            raise serializers.ValidationError(
                "Solita appointments are only at 6:30 AM, 8:30 AM, 10:30 AM, or 2:00 PM."
            )
        return value

    def validate(self, attrs):
        date = attrs.get("date")
        if date and active_bookings_for_date(date).count() >= MAX_BOOKINGS_PER_DAY:
            raise serializers.ValidationError(
                {"date": f"Solita is fully booked on {date}. Please pick another day."}
            )
        return attrs

    def create(self, validated_data):
        service = Service.objects.get(slug=validated_data.pop("service_slug"))
        style = ServiceStyle.objects.get(
            service=service, slug=validated_data.pop("style_slug")
        )
        return Booking.objects.create(
            service=service,
            style=style,
            price=style.price_from,
            **validated_data,
        )


# ──────────────────────────────────────────────
# Orders
# ──────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "customer_name", "customer_email", "customer_phone",
            "shipping_address", "status", "subtotal", "shipping_cost",
            "total", "is_paid", "transaction_id", "items",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class OrderItemCreateSerializer(serializers.Serializer):
    product_slug = serializers.SlugField()
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class OrderCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=30)
    shipping_address = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    items = OrderItemCreateSerializer(many=True)

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item in items_data:
            product = Product.objects.get(slug=item["product_slug"])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                price=item["price"],
            )
        return order


# ──────────────────────────────────────────────
# Gallery
# ──────────────────────────────────────────────

class GalleryPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = GalleryPhoto
        fields = ["id", "image", "image_url", "caption", "is_active", "created_at"]

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
