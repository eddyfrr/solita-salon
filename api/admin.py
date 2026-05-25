from django.contrib import admin
from .models import (
    ProductCategory, Product, ProductImage,
    Service, ServiceStyle,
    Booking, Order, OrderItem, GalleryPhoto,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "in_stock", "is_featured", "is_active"]
    list_filter = ["category", "is_active", "is_featured", "in_stock"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]


class ServiceStyleInline(admin.TabularInline):
    model = ServiceStyle
    extra = 1
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "sort_order"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ServiceStyleInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "client_name", "service", "style", "date", "time",
        "price", "status", "is_paid",
    ]
    list_filter = ["status", "is_paid", "date", "service"]
    search_fields = ["client_name", "client_email", "client_phone"]
    list_editable = ["status", "is_paid"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id", "customer_name", "total", "status", "is_paid", "created_at",
    ]
    list_filter = ["status", "is_paid"]
    search_fields = ["customer_name", "customer_email"]
    list_editable = ["status", "is_paid"]
    inlines = [OrderItemInline]


@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ["__str__", "caption", "is_active", "created_at"]
    list_filter = ["is_active"]
    list_editable = ["is_active"]
