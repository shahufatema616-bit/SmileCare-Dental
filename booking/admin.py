from django.contrib import admin

from .models import Appointment, Clinician, Patient, ReminderLog, TreatmentType


@admin.register(Clinician)
class ClinicianAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "specialty", "photo", "is_active")
    list_filter = ("is_active", "title")
    search_fields = ("name", "specialty")


@admin.register(TreatmentType)
class TreatmentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_minutes")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "phone", "created_at")
    search_fields = ("first_name", "last_name", "email")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "clinician",
        "treatment",
        "appointment_date",
        "start_time",
        "status",
    )
    list_filter = ("status", "appointment_date", "clinician")
    search_fields = ("patient__first_name", "patient__last_name", "patient__email")


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ("appointment", "channel", "status", "scheduled_for", "sent_at")
    list_filter = ("channel", "status")
