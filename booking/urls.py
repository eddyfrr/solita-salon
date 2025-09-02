from django.urls import path
from . import views



urlpatterns = [
    path('', views.service_list, name='service_list'),
    path('book_appointment/', views.book_appointment, name='book_appointment'),
    path('review_booking/', views.review_booking, name='review_booking'),
    path('process_payment/', views.process_payment, name='process_payment'),
    # payment_callback removed - using WhatsApp for payment coordination
    # confirm_payment removed - using WhatsApp flow
    path('success/', views.success_page, name='success_page'),
    path('my_bookings/', views.my_bookings, name='my_bookings'),
    path('login/', views.user_login, name='user_login'),
    path('register/', views.user_register, name='user_register'),
    path('logout/', views.user_logout, name='user_logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
] 