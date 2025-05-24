import cloudinary
import cloudinary.uploader
import os

# ✅ Manually configure Cloudinary (needed if you're not using django-cloudinary-storage)
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dmbyioctu'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '334771536338219'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'OvoJKsPUQAyN5AzzFFpv3qfmRWM')
)

# ✅ Provide a local test image
test_image_path = "/Users/mac/solita_salon/media/services/Knotless_Boho.png"  # Replace this with any small image in your project

try:
    result = cloudinary.uploader.upload(test_image_path)
    print(" Upload successful!")
    print("Image URL:", result["secure_url"])
except Exception as e:
    print(" Upload failed:", str(e))
