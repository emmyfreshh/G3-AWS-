from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('clinician', 'Clinician'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    clinician = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_patients')

    def __str__(self):
        return f"{self.username} ({self.role})"
