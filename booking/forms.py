from django import forms
from .models import Service, ServiceType
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from datetime import datetime

class AppointmentForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'text', 'id': 'id_date'}))
    time = forms.TimeField(widget=forms.TextInput(attrs={'type': 'text', 'id': 'id_time'}), input_formats=['%I:%M %p', '%H:%M'])
    service = forms.ModelChoiceField(queryset=Service.objects.all(), widget=forms.HiddenInput(), required=True)
    service_type = forms.ModelChoiceField(queryset=ServiceType.objects.none(), label="Type", required=True)

    def clean_time(self):
        time_obj = self.cleaned_data.get('time')
        if time_obj:
            return time_obj
        raise forms.ValidationError('Invalid time format. Please use HH:MM AM/PM (e.g., 2:30 PM) or HH:MM (e.g., 14:30).')

    def __init__(self, *args, **kwargs):
        service_id = kwargs.pop('service_id', None)
        super().__init__(*args, **kwargs)
        if service_id:
            self.fields['service_type'].queryset = ServiceType.objects.filter(service_id=service_id)
            self.fields['service'].initial = service_id

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