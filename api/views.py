from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    ProductCategory, Product, ProductImage,
    Service, ServiceStyle, ServiceStyleImage,
    Booking, Order, OrderItem, GalleryPhoto,
)
from .notifications import (
    send_booking_confirmation,
    send_booking_status_update,
    send_order_confirmation,
)
from .payments import generate_checkout_link, get_tzs_per_usd, ExchangeRateUnavailable
from .serializers import (
    UserSerializer, RegisterSerializer,
    ProductCategorySerializer, ProductSerializer, ProductWriteSerializer, ProductImageSerializer,
    ServiceSerializer, ServiceWriteSerializer,
    ServiceStyleSerializer, ServiceStyleWriteSerializer, ServiceStyleImageSerializer,
    BookingSerializer, BookingCreateSerializer,
    OrderSerializer, OrderItemSerializer, OrderCreateSerializer,
    GalleryPhotoSerializer,
)


# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if user is None:
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )
    refresh = RefreshToken.for_user(user)
    return Response({
        "user": UserSerializer(user).data,
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
    })


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me_view(request):
    return Response(UserSerializer(request.user).data)


# ──────────────────────────────────────────────
# Admin Dashboard Stats
# ──────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def dashboard_stats(request):
    today = timezone.now().date()
    this_month_start = today.replace(day=1)

    todays_bookings = Booking.objects.filter(date=today)
    this_month_bookings = Booking.objects.filter(date__gte=this_month_start)
    pending_bookings = Booking.objects.filter(status="pending")

    this_month_orders = Order.objects.filter(created_at__date__gte=this_month_start)
    monthly_revenue = (
        this_month_orders.filter(is_paid=True).aggregate(total=Sum("total"))["total"] or 0
    )
    booking_revenue = (
        this_month_bookings.filter(is_paid=True).aggregate(total=Sum("price"))["total"] or 0
    )

    return Response({
        "todays_bookings": todays_bookings.count(),
        "pending_bookings": pending_bookings.count(),
        "monthly_bookings": this_month_bookings.count(),
        "monthly_orders": this_month_orders.count(),
        "monthly_revenue": float(monthly_revenue + booking_revenue),
        "total_products": Product.objects.filter(is_active=True).count(),
        "total_services": Service.objects.filter(is_active=True).count(),
        "recent_bookings": BookingSerializer(
            todays_bookings[:5], many=True
        ).data,
        "recent_orders": OrderSerializer(
            Order.objects.all()[:5], many=True
        ).data,
    })


# ──────────────────────────────────────────────
# Products
# ──────────────────────────────────────────────

class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProductWriteSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        qs = Product.objects.select_related("category").prefetch_related("images")
        # Public users only see active products
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        # Filter by category
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)
        # Filter featured
        featured = self.request.query_params.get("featured")
        if featured == "true":
            qs = qs.filter(is_featured=True)
        return qs


class ProductImageViewSet(viewsets.ModelViewSet):
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return ProductImage.objects.filter(product__slug=self.kwargs["product_slug"])

    def perform_create(self, serializer):
        product = Product.objects.get(slug=self.kwargs["product_slug"])
        serializer.save(product=product)


# ──────────────────────────────────────────────
# Services
# ──────────────────────────────────────────────

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ServiceWriteSerializer
        return ServiceSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        qs = Service.objects.prefetch_related("styles")
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs


class ServiceStyleViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ServiceStyleWriteSerializer
        return ServiceStyleSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        qs = ServiceStyle.objects.filter(
            service__slug=self.kwargs["service_slug"]
        )
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        service = Service.objects.get(slug=self.kwargs["service_slug"])
        serializer.save(service=service)


class ServiceStyleImageViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceStyleImageSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return ServiceStyleImage.objects.filter(
            style__service__slug=self.kwargs["service_slug"],
            style__slug=self.kwargs["style_slug"],
        )

    def perform_create(self, serializer):
        style = ServiceStyle.objects.get(
            service__slug=self.kwargs["service_slug"],
            slug=self.kwargs["style_slug"],
        )
        serializer.save(style=style)


# ──────────────────────────────────────────────
# Bookings
# ──────────────────────────────────────────────

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        send_booking_confirmation(booking)

        data = BookingSerializer(booking).data

        # Generate ClickPesa checkout URL
        import time as _time
        checkout_currency = request.data.get("checkout_currency", "TZS")
        # ClickPesa only supports TZS and USD
        if checkout_currency not in ("TZS", "USD"):
            checkout_currency = "USD"
        try:
            amount = float(booking.price)
            if checkout_currency == "USD":
                amount = round(amount / get_tzs_per_usd(), 2)
            result = generate_checkout_link(
                amount=amount,
                order_reference=f"BK{booking.id}T{int(_time.time())}",
                currency=checkout_currency,
                customer_name=booking.client_name,
                customer_email=booking.client_email,
                customer_phone=booking.client_phone,
            )
            if result["success"]:
                data["checkout_url"] = result["checkout_url"]
            else:
                data["payment_error"] = result.get("error", "Payment gateway error")
        except ExchangeRateUnavailable as exc:
            data["payment_error"] = str(exc)
        except Exception as exc:
            data["payment_error"] = "Payment service temporarily unavailable. Please try again."

        return Response(data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        qs = Booking.objects.select_related("service", "style")
        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def availability(self, request):
        """Return per-date capacity info so the booking page can disable full days.

        Query params: ?date=YYYY-MM-DD (single day) or ?date_from=&date_to= (range).
        """
        from .serializers import (
            ALLOWED_BOOKING_TIMES,
            MAX_BOOKINGS_PER_DAY,
            active_bookings_for_date,
        )
        from datetime import datetime as _dt

        slot_labels = {
            t.strftime("%H:%M:%S"): t.strftime("%I:%M %p").lstrip("0")
            for t in ALLOWED_BOOKING_TIMES
        }

        def day_payload(date):
            qs = active_bookings_for_date(date)
            booked_total = qs.count()
            per_slot = {
                t.strftime("%H:%M:%S"): qs.filter(time=t).count()
                for t in ALLOWED_BOOKING_TIMES
            }
            return {
                "date": date.isoformat(),
                "max_per_day": MAX_BOOKINGS_PER_DAY,
                "booked": booked_total,
                "remaining": max(MAX_BOOKINGS_PER_DAY - booked_total, 0),
                "is_full": booked_total >= MAX_BOOKINGS_PER_DAY,
                "slot_labels": slot_labels,
                "slot_counts": per_slot,
            }

        single = request.query_params.get("date")
        if single:
            try:
                d = _dt.strptime(single, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(day_payload(d))

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from and date_to:
            try:
                start = _dt.strptime(date_from, "%Y-%m-%d").date()
                end = _dt.strptime(date_to, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)
            if (end - start).days > 92:
                return Response({"error": "Range too large (max 92 days)."},
                                status=status.HTTP_400_BAD_REQUEST)
            days = []
            cur = start
            while cur <= end:
                days.append(day_payload(cur))
                cur += timedelta(days=1)
            return Response({"max_per_day": MAX_BOOKINGS_PER_DAY, "days": days})

        return Response(
            {"error": "Provide ?date=YYYY-MM-DD or ?date_from=&date_to="},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        booking.status = Booking.Status.CONFIRMED
        booking.save()
        send_booking_status_update(booking)
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        booking.status = Booking.Status.CANCELLED
        booking.save()
        send_booking_status_update(booking)
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        booking = self.get_object()
        booking.status = Booking.Status.COMPLETED
        booking.save()
        send_booking_status_update(booking)
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        booking = self.get_object()
        booking.is_paid = True
        booking.save()
        return Response(BookingSerializer(booking).data)


# ──────────────────────────────────────────────
# Orders
# ──────────────────────────────────────────────

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related("items__product")

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        send_order_confirmation(order)
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get("status")
        if new_status in dict(Order.Status.choices):
            order.status = new_status
            order.save()
            return Response(OrderSerializer(order).data)
        return Response(
            {"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST
        )


# ──────────────────────────────────────────────
# Gallery
# ──────────────────────────────────────────────

class GalleryViewSet(viewsets.ModelViewSet):
    queryset = GalleryPhoto.objects.all()
    serializer_class = GalleryPhotoSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        qs = GalleryPhoto.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs


# ──────────────────────────────────────────────
# Payments (ClickPesa)
# ──────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def initiate_payment(request):
    """Initiate a ClickPesa payment for a booking or order."""
    payment_type = request.data.get("type")  # "booking" or "order"
    record_id = request.data.get("id")
    # Currency from frontend — ClickPesa only supports TZS and USD
    checkout_currency = request.data.get("currency", "TZS")
    if checkout_currency not in ("TZS", "USD"):
        checkout_currency = "USD"
    # If frontend sent a pre-converted amount, use it; otherwise convert
    frontend_amount = request.data.get("amount")

    if not payment_type or not record_id:
        return Response(
            {"error": "type and id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    import time as _time

    try:
        if payment_type == "booking":
            try:
                booking = Booking.objects.select_related("service", "style").get(pk=record_id)
            except Booking.DoesNotExist:
                return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

            amount = float(booking.price)
            if checkout_currency == "USD":
                amount = float(frontend_amount) if frontend_amount else round(amount / get_tzs_per_usd(), 2)
            result = generate_checkout_link(
                amount=amount,
                order_reference=f"BK{booking.id}T{int(_time.time())}",
                currency=checkout_currency,
                customer_name=booking.client_name,
                customer_email=booking.client_email,
                customer_phone=booking.client_phone,
            )

        elif payment_type == "order":
            try:
                order = Order.objects.get(pk=record_id)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

            amount = float(order.total)
            if checkout_currency == "USD":
                amount = float(frontend_amount) if frontend_amount else round(amount / get_tzs_per_usd(), 2)
            result = generate_checkout_link(
                amount=amount,
                order_reference=f"OR{order.id}T{int(_time.time())}",
                currency=checkout_currency,
                customer_name=order.customer_name,
                customer_email=order.customer_email,
                customer_phone=order.customer_phone,
            )
        else:
            return Response(
                {"error": "type must be 'booking' or 'order'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except ExchangeRateUnavailable as exc:
        return Response(
            {"error": str(exc)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if result["success"]:
        return Response({"checkout_url": result["checkout_url"]})
    else:
        return Response(
            {"error": result["error"]},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def payment_callback(request):
    """Handle ClickPesa payment callback/webhook."""
    import json
    data = request.data
    logger = __import__("logging").getLogger(__name__)
    logger.info(f"ClickPesa callback received: {json.dumps(data, default=str)}")

    reference = data.get("reference", "")
    payment_status = data.get("status", "").lower()
    transaction_id = data.get("transaction_id", "")

    if payment_status in ("success", "completed", "paid"):
        if reference.startswith("BOOKING-"):
            booking_id = int(reference.split("-")[1])
            try:
                booking = Booking.objects.get(pk=booking_id)
                booking.is_paid = True
                booking.transaction_id = transaction_id
                booking.save()
                logger.info(f"Booking #{booking_id} marked as paid")
            except Booking.DoesNotExist:
                logger.error(f"Booking #{booking_id} not found for callback")

        elif reference.startswith("ORDER-"):
            order_id = int(reference.split("-")[1])
            try:
                order = Order.objects.get(pk=order_id)
                order.is_paid = True
                order.transaction_id = transaction_id
                order.save()
                send_order_confirmation(order)
                logger.info(f"Order #{order_id} marked as paid")
            except Order.DoesNotExist:
                logger.error(f"Order #{order_id} not found for callback")

    return Response({"status": "received"})
