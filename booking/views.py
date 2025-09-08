from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Service, ServiceType, Appointment, ClientPhoto
from .forms import AppointmentForm, RegisterForm
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib import messages
import urllib.parse


def service_list(request):
    services = Service.objects.all()
    client_photos = ClientPhoto.objects.filter(is_active=True)
    print(f"[service_list] Services: {list(services)}")
    print(f"[service_list] Client Photos: {list(client_photos)}")
    return render(request, 'booking/service_list.html', {
        'services': services,
        'client_photos': client_photos
    })

@login_required
def book_appointment(request):
    services = Service.objects.all()
    selected_service = None
    form = None

    if request.method == "POST":
        print(f"[book_appointment] Received POST request: {request.POST}, User: {request.user.username}")
        service_id = request.POST.get('service_id')
        if service_id:
            selected_service = get_object_or_404(Service, id=service_id)
            form = AppointmentForm(request.POST, service_id=service_id)
            print(f"[book_appointment] Form data: service_id={service_id}, service={request.POST.get('service')}, service_type={request.POST.get('service_type')}, date={request.POST.get('date')}, time={request.POST.get('time')}")
            if form.is_valid():
                date_str = form.cleaned_data['date'].strftime('%Y-%m-%d')
                time_obj = form.cleaned_data['time']
                time_str = time_obj.strftime('%H:%M:%S')
                service_type = form.cleaned_data['service_type']
                print(f"[book_appointment] Form valid, redirecting with date: {date_str}, time: {time_str}, type: {service_type}")
                return render(request, 'booking/redirect_to_review.html', {
                    'service_id': selected_service.id,
                    'service_type_id': service_type.id,
                    'date': date_str,
                    'time': time_str
                })
            else:
                print(f"[book_appointment] Form validation failed: {form.errors}")
        else:
            print("[book_appointment] No service_id in POST")
    else:
        service_id = request.GET.get('service_id')
        if service_id:
            selected_service = get_object_or_404(Service, id=service_id)
            form = AppointmentForm(service_id=service_id, initial={'service': selected_service})

    print("[book_appointment] Rendering service_list.html")
    return render(request, 'booking/service_list.html', {
        'services': services,
        'selected_service': selected_service,
        'form': form
    })

@login_required
def review_booking(request):
    if request.method == "POST":
        service_id = request.POST.get('service_id')
        service_type_id = request.POST.get('service_type_id')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')

        print(f"[review_booking] Received POST: service_id={service_id}, service_type_id={service_type_id}, date={date_str}, time={time_str}, User: {request.user.username}")

        if not all([service_id, service_type_id, date_str, time_str]):
            print("[review_booking] Missing required fields")
            return redirect('service_list')

        try:
            service = get_object_or_404(Service, id=service_id)
            service_type = get_object_or_404(ServiceType, id=service_type_id)
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
            appointment = Appointment.objects.create(
                user=request.user,
                service=service,
                service_type=service_type,
                date=date_obj,
                time=time_obj,
                price=service_type.price
            )
            print(f"[review_booking] Appointment Created - ID: {appointment.id}, User: {appointment.user.username}, Service: {appointment.service.name}, Type: {appointment.service_type.type_name}")
            time_display = time_obj.strftime('%I:%M %p')
            print(f"[review_booking] Rendering review_booking.html with appointment_id={appointment.id}")
            return render(request, 'booking/review_booking.html', {
                'service': service,
                'service_type': service_type,
                'date': date_obj,
                'time': time_obj,
                'time_display': time_display,
                'appointment_id': appointment.id
            })
        except Exception as e:
            print(f"[review_booking] Error: {str(e)}")
            return redirect('service_list')

    print("[review_booking] Redirecting to service_list")
    return redirect('service_list')

# ClickPesa integration removed - now using WhatsApp for payment coordination

@login_required
def process_payment(request):
    if request.method == "POST":
        print(f"[process_payment] Received POST request: {request.POST}")

        if 'confirm_payment' in request.POST:
            service_id = request.POST.get('service_id')
            service_type_id = request.POST.get('service_type_id')
            date_str = request.POST.get('date')
            time_str = request.POST.get('time')
            appointment_id = request.POST.get('appointment_id')

            print(f"[process_payment] Confirm Payment - service_id={service_id}, service_type_id={service_type_id}, date={date_str}, time={time_str}, appointment_id={appointment_id}, User: {request.user.username}")

            if not appointment_id:
                appointment_id = request.session.get('appointment_id')
                if not appointment_id:
                    print("[process_payment] Missing appointment_id in confirm_payment")
                    return redirect('service_list')

            appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
            service = get_object_or_404(Service, id=service_id) if service_id else appointment.service
            service_type = get_object_or_404(ServiceType, id=service_type_id) if service_type_id else appointment.service_type
            date_str = date_str or appointment.date.strftime('%Y-%m-%d')
            time_str = time_str or appointment.time.strftime('%H:%M:%S')

            if not all([service_id, service_type_id, date_str, time_str]):
                print("[process_payment] Missing required fields (excluding appointment_id)")
                return redirect('service_list')

            # Create WhatsApp message with booking details
            customer_name = request.user.get_full_name() or request.user.username
            formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
            formatted_time = datetime.strptime(time_str, '%H:%M:%S').strftime('%I:%M %p')
            
            whatsapp_message = f"""Hello! I would like to confirm my booking and get payment details:

📅 *Booking Details:*
• Customer: {customer_name}
• Service: {service.name} - {service_type.type_name}
• Date: {formatted_date}
• Time: {formatted_time}
• Price: TZS {service_type.price:,.0f}
• Booking ID: SOLITA{appointment.id}

Please send me the payment details to complete my booking. Thank you!"""

            # WhatsApp Business number from settings
            whatsapp_number = getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', '255745636924')
            
            # Create WhatsApp URL
            encoded_message = urllib.parse.quote(whatsapp_message)
            whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"
            
            # Mark appointment as pending payment
            appointment.transaction_id = f"WHATSAPP_{appointment.id}"
            appointment.save()
            
            # Store WhatsApp URL in session for the success page
            request.session['whatsapp_url'] = whatsapp_url
            request.session['appointment_id'] = appointment.id
            
            print(f"[process_payment] Redirecting to WhatsApp: {whatsapp_url}")
            return redirect(whatsapp_url)

        appointment_id = request.POST.get('appointment_id')
        if not appointment_id:
            print("[process_payment] Missing appointment_id in initial submission")
            return redirect('service_list')

        appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
        service = appointment.service
        service_type = appointment.service_type
        date_str = appointment.date.strftime('%Y-%m-%d')
        time_str = appointment.time.strftime('%H:%M:%S')

        print(f"[process_payment] Rendering payment page - appointment_id={appointment_id}, User: {request.user.username}")

        return render(request, 'booking/payment.html', {
            'service': service,
            'service_type': service_type,
            'date': appointment.date,
            'time': time_str,
            'time_display': appointment.time.strftime('%I:%M %p'),
            'appointment_id': appointment_id
        })

    appointment_id = request.GET.get('appointment_id')
    if not appointment_id:
        print("[process_payment] Missing appointment_id in GET request")
        return redirect('service_list')

    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    service = appointment.service
    service_type = appointment.service_type
    date_str = appointment.date.strftime('%Y-%m-%d')
    time_str = appointment.time.strftime('%H:%M:%S')

    print(f"[process_payment] Rendering payment page (GET) - appointment_id={appointment_id}, User: {request.user.username}")

    return render(request, 'booking/payment.html', {
        'service': service,
        'service_type': service_type,
        'date': appointment.date,
        'time': time_str,
        'time_display': appointment.time.strftime('%I:%M %p'),
        'appointment_id': appointment_id
    })

# Payment callback removed - manual payment confirmation via WhatsApp

# confirm_payment function removed - payment flow now goes through WhatsApp

@login_required
def success_page(request):
    return render(request, 'booking/success.html')

@login_required
def my_bookings(request):
    appointments = Appointment.objects.filter(user=request.user).order_by('-date', '-time')
    print(f"[my_bookings] User: {request.user.username}, Appointments: {list(appointments)}")
    return render(request, 'booking/my_bookings.html', {'appointments': appointments})

def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            return render(request, 'booking/login.html', {
                'error': 'Please enter both username and password.'
            })
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            print(f"[user_login] User {username} logged in successfully")
            return redirect('service_list')
        else:
            print(f"[user_login] Failed login attempt for username: {username}")
            # Check if user exists to provide more specific error
            try:
                User.objects.get(username=username)
                error_message = 'Incorrect password. Please check your password and try again.'
            except User.DoesNotExist:
                error_message = 'Username not found. Please check your username or register for a new account.'
            
            return render(request, 'booking/login.html', {'error': error_message})
    return render(request, 'booking/login.html')

def user_register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('service_list')
        else:
            return render(request, 'booking/register.html', {'form': form})
    else:
        form = RegisterForm()
    return render(request, 'booking/register.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('user_login')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'Please enter your email address.')
            return redirect('forgot_password')
            
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{request.scheme}://{request.get_host()}/reset-password/{uid}/{token}/"
            
            print(f"[forgot_password] Sending reset email to: {email}")
            print(f"[forgot_password] Reset link: {reset_link}")
            
            send_mail(
                subject='Solita Salon - Password Reset Request',
                message=f'Hello,\n\nYou requested a password reset for your Solita Salon account.\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link will expire in 24 hours.\n\nIf you did not request this, please ignore this email.\n\nBest regards,\nSolita Salon Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #f5d0e6;">Solita Salon - Password Reset</h2>
                    <p>Hello,</p>
                    <p>You requested a password reset for your Solita Salon account.</p>
                    <p>Click the button below to reset your password:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #f5d0e6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset Password</a>
                    </div>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666;">{reset_link}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you did not request this, please ignore this email.</p>
                    <br>
                    <p>Best regards,<br>Solita Salon Team</p>
                </div>
                ''',
                fail_silently=False,
            )
            messages.success(request, 'Password reset link sent to your email. Please check your inbox and spam folder.')
            print(f"[forgot_password] Email sent successfully to: {email}")
            return redirect('forgot_password')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
            print(f"[forgot_password] User not found for email: {email}")
            return redirect('forgot_password')
            
        except Exception as e:
            messages.error(request, f'Failed to send email. Please try again later.')
            print(f"[forgot_password] Email error: {str(e)}")
            import traceback
            traceback.print_exc()
            return redirect('forgot_password')
            
    return render(request, 'booking/forgot_password.html')

def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
        print(f"[reset_password] Found user: {user.username} for uid: {uid}")
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        print(f"[reset_password] Error decoding uid or finding user: {str(e)}")
        user = None

    if user and default_token_generator.check_token(user, token):
        print(f"[reset_password] Token is valid for user: {user.username}")
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not new_password:
                messages.error(request, 'Please enter a new password.')
                return render(request, 'booking/reset_password.html', {'uidb64': uidb64, 'token': token})
            
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'booking/reset_password.html', {'uidb64': uidb64, 'token': token})
                
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'booking/reset_password.html', {'uidb64': uidb64, 'token': token})
            
            try:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password reset successfully. You can now log in with your new password.')
                print(f"[reset_password] Password successfully reset for user: {user.username}")
                return redirect('user_login')
            except Exception as e:
                messages.error(request, 'Error saving new password. Please try again.')
                print(f"[reset_password] Error saving password: {str(e)}")
                return render(request, 'booking/reset_password.html', {'uidb64': uidb64, 'token': token})
                
        return render(request, 'booking/reset_password.html', {'uidb64': uidb64, 'token': token})
    else:
        print(f"[reset_password] Invalid or expired token for user: {user.username if user else 'None'}")
        messages.error(request, 'Invalid or expired reset link. Please request a new password reset.')
        return redirect('forgot_password')