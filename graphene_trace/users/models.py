from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    ROLE_CHOICES = [
        ("patient", "Patient"),
        ("clinician", "Clinician"),
        ("admin", "Admin"),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="patient")

    clinician = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_patients",
        limit_choices_to={"role": "clinician"},
    )

    patient_id_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        help_text="Auto-generated patient identifier, e.g. P-000001",
    )

    clinician_id_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        editable=False,
        help_text="Auto-generated clinician identifier, e.g. C-000001",
    )

    def clean(self):
        super().clean()

        if self.role == "patient" and self.clinician_id_number:
            raise ValidationError(
                {"clinician_id_number": "Clinician ID should be empty for patients."}
            )

        if self.role == "clinician" and self.patient_id_number:
            raise ValidationError(
                {"patient_id_number": "Patient ID should be empty for clinicians."}
            )

        if self.role == "admin":
            if self.patient_id_number:
                raise ValidationError(
                    {"patient_id_number": "Admin should not have a patient ID."}
                )
            if self.clinician_id_number:
                raise ValidationError(
                    {"clinician_id_number": "Admin should not have a clinician ID."}
                )

    def __str__(self):
        return f"{self.username} ({self.role})"


def _format_patient_id(pk: int) -> str:
    return f"P-{pk:06d}"


def _format_clinician_id(pk: int) -> str:
    return f"C-{pk:06d}"


@receiver(post_save, sender=User)
def ensure_role_id_number(sender, instance: User, created: bool, **kwargs):
    """
    After a user is created, assign an ID number based on role.
    Uses update() to avoid recursion.
    """
    if not created:
        return

    if instance.role == "patient" and not instance.patient_id_number:
        sender.objects.filter(pk=instance.pk).update(
            patient_id_number=_format_patient_id(instance.pk),
            clinician_id_number=None,
        )

    elif instance.role == "clinician" and not instance.clinician_id_number:
        sender.objects.filter(pk=instance.pk).update(
            clinician_id_number=_format_clinician_id(instance.pk),
            patient_id_number=None,
        )

    elif instance.role == "admin":
        sender.objects.filter(pk=instance.pk).update(
            patient_id_number=None,
            clinician_id_number=None,
        )