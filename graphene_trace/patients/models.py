from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class PressureData(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pressure_data')
    timestamp = models.DateTimeField(default=timezone.now)
    pressure_value = models.FloatField()  # in mmHg or appropriate unit
    sensor_location = models.CharField(max_length=50)  # e.g., 'left_hip', 'right_shoulder'

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.patient.username} - {self.sensor_location} at {self.timestamp}"

class Comment(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    clinician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='clinician_comments')
    pressure_data = models.ForeignKey(PressureData, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    is_reply = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Comment by {self.patient.username if not self.clinician else self.clinician.username} at {self.timestamp}"

class Notification(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Notification for {self.patient.username}: {self.message[:50]}"

@receiver(post_save, sender=PressureData)
def check_high_pressure(sender, instance, created, **kwargs):
    if created and instance.pressure_value > 100:  # Assuming 100 is high
        Notification.objects.create(
            patient=instance.patient,
            message=f"High pressure detected at {instance.sensor_location}: {instance.pressure_value}"
        )
        # Send email if email is set
        if instance.patient.email:
            from django.core.mail import send_mail
            send_mail(
                'High Pressure Alert',
                f"High pressure detected: {instance.pressure_value} at {instance.sensor_location}",
                'noreply@graphenetrace.com',
                [instance.patient.email],
                fail_silently=True,
            )
