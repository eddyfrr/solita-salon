from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from datetime import datetime

class AppointmentForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'text', 'id': 'id_date'}))
    time = forms.CharField(widget=forms.TextInput(attrs={'type': 'text', 'id': 'id_time'}))

    def clean_time(self):
        time_str = self.cleaned_data.get('time')
        try:
            # Handle AM/PM format (e.g., "12:00 PM")
            if 'AM' in time_str or 'PM' in time_str:
                time_obj = datetime.strptime(time_str, '%I:%M %p').time()
            else:
                # Handle 24-hour format (e.g., "14:30")
                time_obj = datetime.strptime(time_str, '%H:%M').time()
            return time_obj
        except ValueError:
            raise forms.ValidationError('Invalid time format. Please use HH:MM AM/PM (e.g., 2:30 PM).')

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = (
            "Your password must be at least 8 characters long, "
            "contain at least one letter and one number, "
            "cannot be too common (e.g., 'password123'), "
            "and should not be too similar to your username or email."
        )
        self.fields['password2'].help_text = (
            "Enter the same password as above, for verification."
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.lower().endswith('@gmail.com'):
            raise forms.ValidationError('Please use a Gmail address (e.g., your-email@gmail.com).')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user