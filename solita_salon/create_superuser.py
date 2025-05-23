import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solita_salon.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='solita_admin').exists():
    User.objects.create_superuser('solita_admin', 'edmundrwegasira@gmail.com', 'solita123')
    print("Superuser created successfully!")
else:
    print("Superuser already exists!")
