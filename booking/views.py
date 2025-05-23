from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import Service, Appointment
from .forms import AppointmentForm, RegisterForm
from datetime import datetime
import requests
from django.conf import settings
import uuid
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib import messages
import certifi
import ssl
from django.core.mail.backends.smtp import EmailBackend



def service_list(request):
    services = Service.objects.all()
    print(f"[service_list] Services: {list(services)}")
    return render(request, 'booking/service_list.html', {'services': services})

@login_required
def book_appointment(request):
    services = Service.objects.all()
    selected_service = None
    form = AppointmentForm()

    if request.method == "POST":
        print(f"[book_appointment] Received POST request: {request.POST}, User: {request.user.username}")
        if 'service_id' in request.POST:
            selected_service = get_object_or_404(Service, id=request.POST['service_id'])

        form = AppointmentForm(request.POST)
        if form.is_valid() and selected_service:
            date_str = form.cleaned_data['date'].strftime('%Y-%m-%d')
            time_obj = form.cleaned_data['time']
            time_str = time_obj.strftime('%H:%M:%S')
            print(f"[book_appointment] Form valid, redirecting to review_booking with date: {date_str}, time: {time_str}")
            return render(request, 'booking/redirect_to_review.html', {
                'service_id': selected_service.id,
                'date': date_str,
                'time': time_str
            })
        else:
            print(f"[book_appointment] Form validation failed: {form.errors}")

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
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')

        print(f"[review_booking] Received POST request: service_id={service_id}, date={date_str}, time={time_str}, User: {request.user.username}")

        if not all([service_id, date_str, time_str]):
            print("[review_booking] Missing required fields")
            return redirect('service_list')

        try:
            service = get_object_or_404(Service, id=service_id)
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
            appointment = Appointment.objects.create(
                user=request.user,
                service=service,
                date=date_obj,
                time=time_obj
            )
            print(f"[review_booking] Appointment Created - ID: {appointment.id}, User: {appointment.user.username}, Service: {appointment.service.name}")
            time_display = time_obj.strftime('%I:%M %p')
            print(f"[review_booking] Rendering review_booking.html with appointment_id={appointment.id}")
            return render(request, 'booking/review_booking.html', {
                'service': service,
                'date': date_obj,
                'time': time_str,
                'time_display': time_display,
                'appointment_id': appointment.id
            })
        except Exception as e:
            print(f"[review_booking] Error: {str(e)}")
            return redirect('service_list')

    print("[review_booking] Redirecting to service_list")
    return redirect('service_list')

def generate_clickpesa_token():
    url = f"{settings.CLICKPESA_API_URL}/third-parties/generate-token"
    headers = {
        "client-id": settings.CLICKPESA_CLIENT_ID,
        "api-key": settings.CLICKPESA_API_KEY
    }
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        token_data = response.json()
        print(f"[generate_clickpesa_token] Full response: {token_data}")
        token = token_data.get("token")
        if not token:
            print("[generate_clickpesa_token] No token in response")
            raise ValueError("Failed to generate ClickPesa token")
        print(f"[generate_clickpesa_token] Generated token: {token}")
        return token
    except requests.exceptions.RequestException as e:
        print(f"[generate_clickpesa_token] Error: {str(e)} - Response: {response.text if 'response' in locals() else 'No response'}")
        raise

@login_required
def process_payment(request):
    if request.method == "POST":
        print(f"[process_payment] Received POST request: {request.POST}")

        if 'confirm_payment' in request.POST:
            service_id = request.POST.get('service_id')
            date_str = request.POST.get('date')
            time_str = request.POST.get('time')
            appointment_id = request.POST.get('appointment_id')

            print(f"[process_payment] Confirm Payment - service_id={service_id}, date={date_str}, time={time_str}, appointment_id={appointment_id}, User: {request.user.username}")

            if not appointment_id:
                appointment_id = request.session.get('appointment_id')
                if not appointment_id:
                    print("[process_payment] Missing appointment_id in confirm_payment")
                    return redirect('service_list')

            appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
            service = get_object_or_404(Service, id=service_id) if service_id else appointment.service
            date_str = date_str or appointment.date.strftime('%Y-%m-%d')
            time_str = time_str or appointment.time.strftime('%H:%M:%S')

            if not all([service_id, date_str, time_str]):
                print("[process_payment] Missing required fields (excluding appointment_id)")
                return redirect('service_list')

            url = "https://api.clickpesa.com/third-parties/checkout-link/generate-checkout-url"
            payload = {
                "totalPrice": str(service.price),
                "orderReference": f"SOLITA{appointment.id}",
                "orderCurrency": "TZS",
                "customerName": request.user.get_full_name() or request.user.username,
                "customerEmail": request.user.email or "default@example.com",
                "customerPhone": "255745636924",
                "successUrl": settings.CLICKPESA_SUCCESS_URL,
                "failureUrl": settings.CLICKPESA_FAILURE_URL
            }

            try:
                access_token = generate_clickpesa_token()
            except Exception as e:
                print(f"[process_payment] Failed to generate token: {str(e)}")
                request.session['appointment_id'] = appointment.id
                return render(request, 'booking/payment.html', {
                    'service': service,
                    'date': datetime.strptime(date_str, '%Y-%m-%d').date(),
                    'time': time_str,
                    'time_display': datetime.strptime(time_str, '%H:%M:%S').strftime('%I:%M %p'),
                    'appointment_id': appointment_id,
                    'error': 'Unable to connect to payment portal. Please try again.'
                })

            headers = {
                "Authorization": access_token,
                "Content-Type": "application/json"
            }

            try:
                response = requests.request("POST", url, json=payload, headers=headers)
                response.raise_for_status()
                checkout_data = response.json()
                print(f"[ClickPesa Response] {checkout_data}")
                checkout_url = checkout_data.get("checkoutLink")
                print(f"[Checkout URL] {checkout_url}")
                if checkout_url:
                    appointment.transaction_id = checkout_data.get("transactionId", "")
                    appointment.save()
                    request.session['appointment_id'] = appointment.id
                    return redirect(checkout_url)
                else:
                    print("[Error] checkoutLink not found in response")
                    request.session['appointment_id'] = appointment.id
                    return render(request, 'booking/payment.html', {
                        'service': service,
                        'date': datetime.strptime(date_str, '%Y-%m-%d').date(),
                        'time': time_str,
                        'time_display': datetime.strptime(time_str, '%H:%M:%S').strftime('%I:%M %p'),
                        'appointment_id': appointment_id,
                        'error': 'Failed to generate payment link. Please try again.'
                    })
            except requests.exceptions.RequestException as e:
                print(f"[ClickPesa Error] {str(e)} - Response: {response.text if 'response' in locals() else 'No response'}")
                request.session['appointment_id'] = appointment.id
                return render(request, 'booking/payment.html', {
                    'service': service,
                    'date': datetime.strptime(date_str, '%Y-%m-%d').date(),
                    'time': time_str,
                    'time_display': datetime.strptime(time_str, '%H:%M:%S').strftime('%I:%M %p'),
                    'appointment_id': appointment_id,
                    'error': 'Unable to connect to payment portal. Please try again.'
                })

        appointment_id = request.POST.get('appointment_id')
        if not appointment_id:
            print("[process_payment] Missing appointment_id in initial submission")
            return redirect('service_list')

        appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
        service = appointment.service
        date_str = appointment.date.strftime('%Y-%m-%d')
        time_str = appointment.time.strftime('%H:%M:%S')

        print(f"[process_payment] Rendering payment page - appointment_id={appointment_id}, User: {request.user.username}")

        return render(request, 'booking/payment.html', {
            'service': service,
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
    date_str = appointment.date.strftime('%Y-%m-%d')
    time_str = appointment.time.strftime('%H:%M:%S')

    print(f"[process_payment] Rendering payment page (GET) - appointment_id={appointment_id}, User: {request.user.username}")

    return render(request, 'booking/payment.html', {
        'service': service,
        'date': appointment.date,
        'time': time_str,
        'time_display': appointment.time.strftime('%I:%M %p'),
        'appointment_id': appointment_id
    })

def payment_callback(request):
    if request.method == "POST":
        data = request.POST
        payment_status = data.get("status")
        transaction_id = data.get("paymentReference")
        order_reference = data.get("orderReference")
        print(f"[payment_callback] Webhook received: {data}")

        if not all([payment_status, transaction_id, order_reference]):
            print("[payment_callback] Missing required fields in webhook payload")
            return HttpResponse(status=400)

        appointment = Appointment.objects.filter(transaction_id=transaction_id).first()
        if not appointment:
            appointment_id = order_reference.split('-')[1] if '-' in order_reference else None
            appointment = Appointment.objects.filter(id=appointment_id).first()

        if appointment:
            if payment_status == "SUCCESS":
                appointment.is_paid = True
                appointment.save()
                print(f"[payment_callback] Appointment updated: ID={appointment.id}, Paid=True")
            elif payment_status == "FAILED":
                appointment.is_paid = False
                appointment.save()
                print(f"[payment_callback] Appointment updated: ID={appointment.id}, Paid=False")
            else:
                print(f"[payment_callback] Unknown payment status: {payment_status}")
            request.session['appointment_id'] = appointment.id
        else:
            print("[payment_callback] Appointment not found")

        return HttpResponse(status=200)

    return HttpResponse(status=400)

@login_required
def confirm_payment(request):
    if request.method == "POST":
        service_id = request.POST.get('service_id')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        print(f"[confirm_payment] Received POST request: service_id={service_id}, date={date_str}, time={time_str}, User: {request.user.username}")

        if not all([service_id, date_str, time_str]):
            print("[confirm_payment] Missing required fields")
            return render(request, 'booking/payment.html', {
                'service': get_object_or_404(Service, id=service_id) if service_id else None,
                'date': date_str,
                'time': time_str,
                'time_display': time_str,
                'error': 'Missing required fields. Please try again.'
            })

        service = get_object_or_404(Service, id=service_id)
        try:
            time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError as e:
            print(f"[confirm_payment] Time parsing error: {e}")
            return render(request, 'booking/payment.html', {
                'service': service,
                'date': date_str,
                'time': time_str,
                'time_display': time_str,
                'error': f'Invalid time format: {time_str}. Expected HH:MM:SS (e.g., 14:30:00).'
            })

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError as e:
            print(f"[confirm_payment] Date parsing error: {e}")
            return render(request, 'booking/payment.html', {
                'service': service,
                'date': date_str,
                'time': time_str,
                'time_display': time_obj.strftime('%I:%M %p'),
                'error': f'Invalid date format: {date_str}. Expected YYYY-MM-DD (e.g., 2025-04-30).'
            })

        try:
            appointment = Appointment(
                user=request.user,
                service=service,
                date=date_obj,
                time=time_obj
            )
            print("[confirm_payment] Saving appointment")
            appointment.save()
        except Exception as e:
            print(f"[confirm_payment] Error saving appointment: {e}")
            return render(request, 'booking/payment.html', {
                'service': service,
                'date': date_str,
                'time': time_str,
                'time_display': time_obj.strftime('%I:%M %p'),
                'error': f'Error saving appointment: {str(e)}'
            })

        print("[confirm_payment] Redirecting to success_page")
        return redirect('success_page')

    print("[confirm_payment] Redirecting to service_list")
    return redirect('service_list')

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
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('service_list')
        else:
            return render(request, 'booking/login.html', {'error': 'Invalid username or password'})
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

@login_required
def user_logout(request):
    logout(request)
    return redirect('user_login')

def forgot_password(request):
      if request.method == 'POST':
          email = request.POST.get('email')
          try:
              user = User.objects.get(email=email)
              token = default_token_generator.make_token(user)
              uid = urlsafe_base64_encode(force_bytes(user.pk))
              reset_link = f"{request.scheme}://{request.get_host()}/reset-password/{uid}/{token}/"
              send_mail(
                  subject='Password Reset Request',
                  message=f'Click the link to reset your password: {reset_link}\nThis link will expire in 1 hour.',
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[email],
                  html_message=f'<p>Click <a href="{reset_link}">here</a> to reset your password.</p><>This link will expire in 1 hour.</p><p><a href="{unsubscribe}">Unsubscribe</a></p>',
                  extra_tags={'isTransactional': True}
              )
              messages.success(request, 'Password reset link sent to your email.')
              return redirect('forgot_password')
          except User.DoesNotExist:
              messages.error(request, 'Email not found.')
              return redirect('forgot_password')
          except User.MultipleObjectsReturned:
              messages.error(request, 'Multiple accounts found for this email. Please contact support.')
              return redirect('forgot_password')
          except Exception as e:
              messages.error(request, f'Failed to send email: {str(e)}')
              return redirect('forgot_password')
      return render(request, 'booking/forgot_password.html')

def reset_password(request, uidb64, token):
      try:
          uid = urlsafe_base64_decode(uidb64).decode()
          user = User.objects.get(pk=uid)
      except (TypeError, ValueError, OverflowError, User.DoesNotExist):
          user = None

      if user and default_token_generator.check_token(user, token):
          if request.method == 'POST':
              password = request.POST.get('new_password')
              user.set_password(password)
              user.save()
              messages.success(request, 'Password reset successfully. You can now log in.')
              return redirect('user_login')
          return render(request, 'booking/reset_password.html', {'uidb64': uidb64, 'token': token})
      else:
          messages.error(request, 'Invalid or expired link.')
          return redirect('forgot_password')

