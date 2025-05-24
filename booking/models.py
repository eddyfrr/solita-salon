from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import pre_save
import logging
from cloudinary.models import CloudinaryField
# Create your models here.

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField()
    image = CloudinaryField('image')
    
    def __str__(self):
        return self.name
    
class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # Added for ClickPesa
    
    
    def __str__(self):
        return f"{self.user.username} - {self.service.name} on {self.date} at {self.time}"
    
logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Service)
def log_image_upload(sender, instance, **kwargs):
    if instance.image:
        logger.debug(f"Uploading image: {instance.image}")