from django.contrib import admin
from .models import Service, Appointment
# Register your models here.

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'date', 'time', 'created_at')
    list_filter = ('date', 'service')
    search_fields = ('user__username', 'service__name')
    fields = ('name', 'description', 'price', 'image')

admin.site.register(Service)
admin.site.register(Appointment, AppointmentAdmin)

