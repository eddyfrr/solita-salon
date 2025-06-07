from django.contrib import admin
from .models import Service, ServiceType, Appointment

class ServiceTypeInline(admin.TabularInline):
    model = ServiceType
    extra = 1

class ServiceAdmin(admin.ModelAdmin):
    inlines = [ServiceTypeInline]
    list_display = ['name']

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'service_type', 'date', 'time', 'price', 'is_paid', 'created_at')
    list_filter = ('date', 'service', 'is_paid')
    search_fields = ('user__username', 'service__name')

admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceType)
admin.site.register(Appointment, AppointmentAdmin)