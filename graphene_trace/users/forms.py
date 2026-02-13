from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=[('patient', 'Patient'), ('clinician', 'Clinician')], required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2')

class CSVUploadForm(forms.Form):
    patient = forms.ModelChoiceField(queryset=User.objects.filter(role='patient'), label='Select Patient')
    csv_file = forms.FileField(label='Select CSV file')
    date = forms.DateField(label='Date for the data', widget=forms.DateInput(attrs={'type': 'date'}))