from django.contrib import admin
from .models import Service, ServiceType, Appointment, ClientPhoto

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
    list_editable = ('is_paid',)  # Allow quick payment status updates
    actions = ['mark_as_paid', 'mark_as_unpaid']
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(is_paid=True)
        self.message_user(request, f'{updated} appointments marked as paid.')
    mark_as_paid.short_description = "Mark selected appointments as paid"
    
    def mark_as_unpaid(self, request, queryset):
        updated = queryset.update(is_paid=False)
        self.message_user(request, f'{updated} appointments marked as unpaid.')
    mark_as_unpaid.short_description = "Mark selected appointments as unpaid"

class ClientPhotoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'caption', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('caption',)
    list_editable = ('is_active',)
    actions = ['activate_photos', 'deactivate_photos']
    
    def activate_photos(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} photos activated.')
    activate_photos.short_description = "Activate selected photos"
    
    def deactivate_photos(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} photos deactivated.')
    deactivate_photos.short_description = "Deactivate selected photos"

admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceType)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(ClientPhoto, ClientPhotoAdmin)