import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_booking_confirmation(booking):
    """Send booking confirmation email to the customer."""
    subject = f"Booking Confirmed — {booking.style.name} at Solita Beauty Bar"

    date_formatted = booking.date.strftime("%A, %B %d, %Y")
    time_formatted = booking.time.strftime("%I:%M %p")
    price_formatted = f"TSh {booking.price:,.0f}"

    # Build options summary
    options = []
    if booking.selected_length:
        options.append(f"Length: {booking.selected_length}")
    if booking.selected_color:
        options.append(f"Color: {booking.selected_color}")
    if booking.selected_type:
        options.append(f"Type: {booking.selected_type}")
    options_text = " | ".join(options) if options else "Standard"

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0; padding:0; background-color:#FAF0E8; font-family:'Helvetica Neue',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#FAF0E8;">
        <tr><td align="center" style="padding:24px 16px;">
            <table width="560" cellpadding="0" cellspacing="0" style="background:#fff; max-width:560px;">
                <!-- Header -->
                <tr>
                    <td style="background-color:#8B5E3C; padding:32px 24px; text-align:center;">
                        <h1 style="color:#fff; font-size:24px; margin:0; font-weight:400; letter-spacing:0.05em;">Solita</h1>
                        <p style="color:rgba(255,255,255,0.8); font-size:13px; margin:8px 0 0; letter-spacing:0.15em; text-transform:uppercase;">Beauty Bar</p>
                    </td>
                </tr>
                <!-- Body -->
                <tr>
                    <td style="padding:32px 24px;">
                        <p style="font-size:18px; color:#282828; margin:0 0 16px;">Hi {booking.client_name},</p>
                        <p style="font-size:14px; color:#686868; line-height:1.7; margin:0 0 24px;">
                            Your booking has been received! Here are your appointment details:
                        </p>

                        <!-- Details Card -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="background:#FDF8F3; border:1px solid #E8D5C4; border-radius:8px;">
                            <tr>
                                <td style="padding:20px;">
                                    <p style="font-size:13px; color:#8B5E3C; text-transform:uppercase; letter-spacing:0.1em; margin:0 0 14px; font-weight:600;">Appointment Details</p>
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#999; font-size:14px; width:40%;">Service</td>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#282828; font-size:14px; font-weight:500; text-align:right;">{booking.service.name}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#999; font-size:14px;">Style</td>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#282828; font-size:14px; font-weight:500; text-align:right;">{booking.style.name}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#999; font-size:14px;">Options</td>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#282828; font-size:14px; font-weight:500; text-align:right;">{options_text}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#999; font-size:14px;">Date</td>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#282828; font-size:14px; font-weight:500; text-align:right;">{date_formatted}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#999; font-size:14px;">Time</td>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#282828; font-size:14px; font-weight:500; text-align:right;">{time_formatted}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#999; font-size:14px;">Payment</td>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#282828; font-size:14px; font-weight:500; text-align:right;">{booking.get_payment_method_display()}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding:14px 0 4px; border-top:2px solid #E8D5C4; color:#999; font-size:14px;">Estimated Price</td>
                                            <td style="padding:14px 0 4px; border-top:2px solid #E8D5C4; color:#8B5E3C; font-size:18px; font-weight:600; text-align:right;">{price_formatted}</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>

                        <!-- Status Note -->
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:24px;">
                            <tr>
                                <td style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px; padding:14px 16px; font-size:13px; color:#15803d;">
                                    Your booking status is <strong>Pending</strong>. We will confirm your appointment shortly via email or phone.
                                </td>
                            </tr>
                        </table>

                        <p style="font-size:14px; color:#686868; line-height:1.7; margin:24px 0 0;">
                            If you need to reschedule or cancel, please contact us at least 24 hours before your appointment.
                        </p>
                    </td>
                </tr>
                <!-- Footer -->
                <tr>
                    <td style="background:#FAF0E8; padding:20px 24px; text-align:center;">
                        <p style="font-size:12px; color:#999; margin:0 0 4px;">Solita Beauty Bar &middot; Dar es Salaam</p>
                        <p style="font-size:12px; margin:0;"><a href="mailto:hello@solitabeautybar.com" style="color:#8B5E3C; text-decoration:none;">hello@solitabeautybar.com</a></p>
                    </td>
                </tr>
            </table>
        </td></tr>
        </table>
    </body>
    </html>
    """

    plain_message = (
        f"Hi {booking.client_name},\n\n"
        f"Your booking has been received!\n\n"
        f"Service: {booking.service.name} — {booking.style.name}\n"
        f"Options: {options_text}\n"
        f"Date: {date_formatted}\n"
        f"Time: {time_formatted}\n"
        f"Payment: {booking.get_payment_method_display()}\n"
        f"Estimated Price: {price_formatted}\n\n"
        f"Status: Pending — we will confirm shortly.\n\n"
        f"— Solita Beauty Bar"
    )

    try:
        send_mail(subject, "", settings.DEFAULT_FROM_EMAIL, [booking.client_email], html_message=html_message, fail_silently=False)
        logger.info(f"Booking confirmation email sent to {booking.client_email}")
    except Exception as e:
        logger.error(f"Failed to send booking email to {booking.client_email}: {e}")


def send_booking_status_update(booking):
    """Send email when booking status changes (confirmed, cancelled, etc.)."""
    status_messages = {
        "confirmed": {
            "subject": f"Booking Confirmed! — {booking.style.name}",
            "emoji": "✅",
            "color": "#15803d",
            "bg": "#f0fdf4",
            "text": "Great news! Your appointment has been confirmed. We look forward to seeing you!",
        },
        "cancelled": {
            "subject": f"Booking Cancelled — {booking.style.name}",
            "emoji": "❌",
            "color": "#dc2626",
            "bg": "#fef2f2",
            "text": "Your appointment has been cancelled. If this was a mistake, please contact us to rebook.",
        },
        "completed": {
            "subject": f"Thank You! — {booking.style.name}",
            "emoji": "🎉",
            "color": "#8B5E3C",
            "bg": "#FDF8F3",
            "text": "Thank you for visiting Solita Beauty Bar! We hope you loved your look. See you again soon!",
        },
    }

    info = status_messages.get(booking.status)
    if not info:
        return

    date_formatted = booking.date.strftime("%A, %B %d, %Y")
    time_formatted = booking.time.strftime("%I:%M %p")

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0; padding:0; background-color:#FAF0E8; font-family:'Helvetica Neue',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#FAF0E8;">
        <tr><td align="center" style="padding:24px 16px;">
            <table width="560" cellpadding="0" cellspacing="0" style="background:#fff; max-width:560px;">
                <tr>
                    <td style="background-color:#8B5E3C; padding:32px 24px; text-align:center;">
                        <h1 style="color:#fff; font-size:24px; margin:0; font-weight:400; letter-spacing:0.05em;">Solita</h1>
                        <p style="color:rgba(255,255,255,0.8); font-size:13px; margin:8px 0 0; letter-spacing:0.15em; text-transform:uppercase;">Beauty Bar</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding:32px 24px;">
                        <p style="font-size:18px; color:#282828; margin:0 0 20px;">Hi {booking.client_name},</p>
                        <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
                            <tr>
                                <td style="background:{info['bg']}; border-radius:8px; padding:28px 20px; text-align:center;">
                                    <p style="font-size:36px; margin:0 0 10px;">{info['emoji']}</p>
                                    <p style="font-size:18px; color:{info['color']}; font-weight:600; margin:0 0 10px;">{booking.get_status_display()}</p>
                                    <p style="font-size:14px; color:#686868; margin:0; line-height:1.6;">{info['text']}</p>
                                </td>
                            </tr>
                        </table>
                        <table width="100%" cellpadding="0" cellspacing="0" style="background:#FDF8F3; border:1px solid #E8D5C4; border-radius:8px;">
                            <tr>
                                <td style="padding:20px;">
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#999; font-size:14px; width:40%;">Service</td>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#282828; font-size:14px; font-weight:500; text-align:right;">{booking.service.name}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#999; font-size:14px;">Style</td>
                                            <td style="padding:10px 0; border-bottom:1px solid #f0ebe5; color:#282828; font-size:14px; font-weight:500; text-align:right;">{booking.style.name}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding:10px 0; color:#999; font-size:14px;">Date &amp; Time</td>
                                            <td style="padding:10px 0; color:#282828; font-size:14px; font-weight:500; text-align:right;">{date_formatted} at {time_formatted}</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td style="background:#FAF0E8; padding:20px 24px; text-align:center;">
                        <p style="font-size:12px; color:#999; margin:0 0 4px;">Solita Beauty Bar &middot; Dar es Salaam</p>
                        <p style="font-size:12px; margin:0;"><a href="mailto:hello@solitabeautybar.com" style="color:#8B5E3C; text-decoration:none;">hello@solitabeautybar.com</a></p>
                    </td>
                </tr>
            </table>
        </td></tr>
        </table>
    </body>
    </html>
    """

    plain_message = (
        f"Hi {booking.client_name},\n\n"
        f"{info['text']}\n\n"
        f"{booking.service.name} — {booking.style.name}\n"
        f"{date_formatted} at {time_formatted}\n\n"
        f"— Solita Beauty Bar"
    )

    try:
        send_mail(info["subject"], "", settings.DEFAULT_FROM_EMAIL, [booking.client_email], html_message=html_message, fail_silently=False)
        logger.info(f"Status update email ({booking.status}) sent to {booking.client_email}")
    except Exception as e:
        logger.error(f"Failed to send status email to {booking.client_email}: {e}")


def send_order_confirmation(order):
    """Send order confirmation email to the customer."""
    subject = f"Order #{order.id} Confirmed — Solita Beauty Bar"

    items_html = ""
    items_text = ""
    for item in order.items.select_related("product").all():
        items_html += f"""
        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0ebe5; font-size: 14px;">
            <span style="color: #282828;">{item.product.name} x{item.quantity}</span>
            <span style="color: #282828; font-weight: 500;">TSh {item.price * item.quantity:,.0f}</span>
        </div>
        """
        items_text += f"  {item.product.name} x{item.quantity} — TSh {item.price * item.quantity:,.0f}\n"

    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background: #FAF0E8;">
        <div style="max-width: 560px; margin: 0 auto; background: #fff;">
            <div style="background-color: #8B5E3C; padding: 32px 24px; text-align: center;">
                <h1 style="color: #fff; font-size: 24px; margin: 0; font-weight: 400;">Solita</h1>
                <p style="color: rgba(255,255,255,0.8); font-size: 13px; margin: 8px 0 0; letter-spacing: 0.15em; text-transform: uppercase;">Beauty Bar</p>
            </div>
            <div style="padding: 32px 24px;">
                <p style="font-size: 18px; color: #282828;">Hi {order.customer_name},</p>
                <p style="font-size: 14px; color: #686868; line-height: 1.7;">
                    Thank you for your order! Here's your order summary:
                </p>

                <div style="background: #FDF8F3; border: 1px solid #E8D5C4; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h3 style="font-size: 13px; color: #8B5E3C; text-transform: uppercase; letter-spacing: 0.1em; margin: 0 0 14px;">
                        Order #{order.id}
                    </h3>
                    {items_html}
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; font-size: 14px;">
                        <span style="color: #999;">Subtotal</span>
                        <span style="color: #282828;">TSh {order.subtotal:,.0f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; font-size: 14px;">
                        <span style="color: #999;">Shipping</span>
                        <span style="color: #282828;">{"Free" if order.shipping_cost == 0 else f"TSh {order.shipping_cost:,.0f}"}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 12px 0 0; margin-top: 8px; border-top: 2px solid #E8D5C4; font-size: 16px;">
                        <span style="color: #282828; font-weight: 600;">Total</span>
                        <span style="color: #8B5E3C; font-weight: 600;">TSh {order.total:,.0f}</span>
                    </div>
                </div>

                <p style="font-size: 14px; color: #686868;">
                    <strong>Shipping to:</strong> {order.shipping_address}
                </p>
                <p style="font-size: 13px; color: #999;">
                    You'll receive tracking information once your order ships.
                </p>
            </div>
            <div style="background: #FAF0E8; padding: 20px 24px; text-align: center; font-size: 12px; color: #999;">
                Solita Beauty Bar &middot; Dar es Salaam
            </div>
        </div>
    </body>
    </html>
    """

    plain_message = (
        f"Hi {order.customer_name},\n\n"
        f"Thank you for your order #{order.id}!\n\n"
        f"Items:\n{items_text}\n"
        f"Subtotal: TSh {order.subtotal:,.0f}\n"
        f"Shipping: {'Free' if order.shipping_cost == 0 else f'TSh {order.shipping_cost:,.0f}'}\n"
        f"Total: TSh {order.total:,.0f}\n\n"
        f"Shipping to: {order.shipping_address}\n\n"
        f"— Solita Beauty Bar"
    )

    try:
        send_mail(subject, "", settings.DEFAULT_FROM_EMAIL, [order.customer_email], html_message=html_message, fail_silently=False)
        logger.info(f"Order confirmation email sent to {order.customer_email}")
    except Exception as e:
        logger.error(f"Failed to send order email to {order.customer_email}: {e}")
