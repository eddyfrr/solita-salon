from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r"products", views.ProductViewSet, basename="product")
router.register(r"categories", views.ProductCategoryViewSet, basename="category")
router.register(r"services", views.ServiceViewSet, basename="service")
router.register(r"bookings", views.BookingViewSet, basename="booking")
router.register(r"orders", views.OrderViewSet, basename="order")
router.register(r"gallery", views.GalleryViewSet, basename="gallery")

urlpatterns = [
    # Auth
    path("auth/login/", views.login_view, name="api-login"),
    path("auth/register/", views.register_view, name="api-register"),
    path("auth/me/", views.me_view, name="api-me"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Dashboard
    path("dashboard/stats/", views.dashboard_stats, name="dashboard-stats"),

    # Service styles (nested under services)
    path(
        "services/<slug:service_slug>/styles/",
        views.ServiceStyleViewSet.as_view({"get": "list", "post": "create"}),
        name="service-styles-list",
    ),
    path(
        "services/<slug:service_slug>/styles/<slug:slug>/",
        views.ServiceStyleViewSet.as_view({
            "get": "retrieve", "put": "update",
            "patch": "partial_update", "delete": "destroy",
        }),
        name="service-styles-detail",
    ),

    # Service style images (multi-image carousel)
    path(
        "services/<slug:service_slug>/styles/<slug:style_slug>/images/",
        views.ServiceStyleImageViewSet.as_view({"get": "list", "post": "create"}),
        name="service-style-images-list",
    ),
    path(
        "services/<slug:service_slug>/styles/<slug:style_slug>/images/<int:pk>/",
        views.ServiceStyleImageViewSet.as_view({
            "get": "retrieve", "put": "update", "delete": "destroy",
        }),
        name="service-style-images-detail",
    ),

    # Product images (nested under products)
    path(
        "products/<slug:product_slug>/images/",
        views.ProductImageViewSet.as_view({"get": "list", "post": "create"}),
        name="product-images-list",
    ),
    path(
        "products/<slug:product_slug>/images/<int:pk>/",
        views.ProductImageViewSet.as_view({
            "get": "retrieve", "put": "update", "delete": "destroy",
        }),
        name="product-images-detail",
    ),

    # Payments (ClickPesa)
    path("payments/initiate/", views.initiate_payment, name="initiate-payment"),
    path("payments/callback/", views.payment_callback, name="payment-callback"),

    # Router URLs
    path("", include(router.urls)),
]
