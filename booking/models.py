from django.db import models


class Clinician(models.Model):
    name = models.CharField(max_length=120)
    title = models.CharField(max_length=80, default="Dentist")
    specialty = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    photo = models.CharField(
        max_length=120,
        blank=True,
        help_text="Filename inside booking/static/booking/img/",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def photo_static_path(self):
        if self.photo:
            return f"booking/img/{self.photo}"
        return "booking/img/about-team.jpg"


class TreatmentType(models.Model):
    name = models.CharField(max_length=120)
    duration_minutes = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Patient(models.Model):
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Appointment(models.Model):
    STATUS_BOOKED = "booked"
    STATUS_CONFIRMED = "confirmed"
    STATUS_ATTENDED = "attended"
    STATUS_NO_SHOW = "no_show"
    STATUS_CANCELLED = "cancelled"
    STATUS_LATE_CANCEL = "late_cancel"

    STATUS_CHOICES = [
        (STATUS_BOOKED, "Booked"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_ATTENDED, "Attended"),
        (STATUS_NO_SHOW, "No show"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_LATE_CANCEL, "Late cancellation"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    clinician = models.ForeignKey(Clinician, on_delete=models.PROTECT, related_name="appointments")
    treatment = models.ForeignKey(TreatmentType, on_delete=models.PROTECT, related_name="appointments")
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_BOOKED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["appointment_date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["clinician", "appointment_date", "start_time"],
                condition=models.Q(
                    status__in=["booked", "confirmed", "attended"]
                ),
                name="unique_active_clinician_slot",
            )
        ]

    @property
    def is_active_booking(self):
        return self.status in {
            self.STATUS_BOOKED,
            self.STATUS_CONFIRMED,
            self.STATUS_ATTENDED,
        }

    def __str__(self):
        return f"{self.patient} with {self.clinician} on {self.appointment_date} at {self.start_time}"


class ReminderLog(models.Model):
    CHANNEL_EMAIL = "email"
    CHANNEL_SMS = "sms"
    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_SMS, "SMS (simulated)"),
    ]

    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
    ]

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="reminders")
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-scheduled_for"]

    def __str__(self):
        return f"{self.channel} reminder for appointment {self.appointment_id}"
