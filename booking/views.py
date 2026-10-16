from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CancelBookingForm, ManageBookingForm, PatientBookingForm
from .models import Appointment, Clinician, ReminderLog
from .notifications import (
    send_cancellation_notice,
    send_confirmation,
    send_reschedule_notice,
)
from .services import get_available_slots, slot_end_time, upcoming_dates


def home(request):
    clinicians = Clinician.objects.filter(is_active=True)
    return render(request, "booking/home.html", {"clinicians": clinicians})


def developer(request):
    return render(
        request,
        "booking/developer.html",
        {
            "student_name": "Fatemazahera Mahammadhasam Shahu",
            "student_id": "1216169",
            "course_name": "SCI701 Research/Industry Dissertation 2",
            "project_title": "Dental Clinic Appointment Booking and Reminder System",
            "supervisor_name": "Wasif Husain",
        },
    )


def select_clinician(request):
    clinicians = Clinician.objects.filter(is_active=True)
    return render(request, "booking/select_clinician.html", {"clinicians": clinicians})


def select_date(request, clinician_id):
    clinician = get_object_or_404(Clinician, pk=clinician_id, is_active=True)
    request.session["booking_clinician_id"] = clinician.id
    return render(
        request,
        "booking/select_date.html",
        {"clinician": clinician, "dates": upcoming_dates()},
    )


def select_time(request, clinician_id, date_str):
    clinician = get_object_or_404(Clinician, pk=clinician_id, is_active=True)
    appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    request.session["booking_date"] = date_str
    exclude_id = request.session.get("reschedule_appointment_id")
    slots = get_available_slots(
        clinician,
        appointment_date,
        exclude_appointment_id=exclude_id,
    )
    return render(
        request,
        "booking/select_time.html",
        {
            "clinician": clinician,
            "appointment_date": appointment_date,
            "slots": slots,
            "is_reschedule": bool(exclude_id),
        },
    )


def confirm_booking(request):
    clinician_id = request.session.get("booking_clinician_id")
    date_str = request.session.get("booking_date")
    time_str = request.session.get("booking_time")
    reschedule_id = request.session.get("reschedule_appointment_id")

    if not all([clinician_id, date_str, time_str]):
        messages.error(request, "Please start your booking from the beginning.")
        return redirect("booking:select_clinician")

    clinician = get_object_or_404(Clinician, pk=clinician_id, is_active=True)
    appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    start_time = datetime.strptime(time_str, "%H:%M").time()

    if reschedule_id:
        appointment = get_object_or_404(
            Appointment.objects.select_related("patient", "treatment", "clinician"),
            pk=reschedule_id,
        )
        if request.method == "POST":
            available = get_available_slots(
                clinician,
                appointment_date,
                exclude_appointment_id=appointment.id,
            )
            if start_time not in available:
                messages.error(request, "That time slot is no longer available.")
                return redirect(
                    "booking:select_time",
                    clinician_id=clinician.id,
                    date_str=date_str,
                )

            old_date = appointment.appointment_date
            old_time = appointment.start_time
            appointment.clinician = clinician
            appointment.appointment_date = appointment_date
            appointment.start_time = start_time
            appointment.end_time = slot_end_time(
                start_time, appointment.treatment.duration_minutes
            )
            appointment.status = Appointment.STATUS_CONFIRMED
            appointment.save()

            send_reschedule_notice(appointment, old_date, old_time)
            _clear_booking_session(request)
            messages.success(request, "Your appointment has been rescheduled.")
            return redirect("booking:booking_success", appointment_id=appointment.id)

        return render(
            request,
            "booking/confirm_reschedule.html",
            {
                "appointment": appointment,
                "clinician": clinician,
                "appointment_date": appointment_date,
                "start_time": start_time,
            },
        )

    if request.method == "POST":
        form = PatientBookingForm(request.POST)
        if form.is_valid():
            patient = form.save()
            treatment = form.cleaned_data["treatment"]
            end_time = slot_end_time(start_time, treatment.duration_minutes)

            if start_time not in get_available_slots(clinician, appointment_date):
                messages.error(
                    request, "That time slot is no longer available. Please pick another."
                )
                return redirect(
                    "booking:select_time",
                    clinician_id=clinician.id,
                    date_str=date_str,
                )

            appointment = Appointment.objects.create(
                patient=patient,
                clinician=clinician,
                treatment=treatment,
                appointment_date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                status=Appointment.STATUS_CONFIRMED,
            )

            send_confirmation(appointment)
            _clear_booking_session(request)
            return redirect("booking:booking_success", appointment_id=appointment.id)
    else:
        form = PatientBookingForm()

    return render(
        request,
        "booking/confirm.html",
        {
            "form": form,
            "clinician": clinician,
            "appointment_date": appointment_date,
            "start_time": start_time,
        },
    )


def set_time_and_confirm(request, clinician_id, date_str, time_str):
    request.session["booking_clinician_id"] = clinician_id
    request.session["booking_date"] = date_str
    request.session["booking_time"] = time_str
    return redirect("booking:confirm_booking")


def booking_success(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "clinician", "treatment"),
        pk=appointment_id,
    )
    latest_email = (
        appointment.reminders.filter(
            channel=ReminderLog.CHANNEL_EMAIL,
            status=ReminderLog.STATUS_SENT,
        )
        .order_by("-id")
        .first()
    )
    return render(
        request,
        "booking/success.html",
        {
            "appointment": appointment,
            "latest_email": latest_email,
        },
    )


def manage_booking(request):
    appointments = None
    searched = False
    initial_email = request.session.get("manage_email", "")

    if request.method == "POST":
        form = ManageBookingForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            request.session["manage_email"] = email
            appointments = list(
                Appointment.objects.filter(patient__email__iexact=email)
                .select_related("patient", "clinician", "treatment")
                .order_by("-appointment_date", "-start_time", "-created_at")
            )
            searched = True
            if not appointments:
                messages.error(
                    request,
                    "We could not find any bookings for that email address. "
                    "Please check the spelling, or try the email you used when you booked.",
                )
    else:
        form = ManageBookingForm(initial={"email": initial_email} if initial_email else None)
        if initial_email and request.GET.get("show") == "1":
            appointments = list(
                Appointment.objects.filter(patient__email__iexact=initial_email)
                .select_related("patient", "clinician", "treatment")
                .order_by("-appointment_date", "-start_time", "-created_at")
            )
            searched = True

    return render(
        request,
        "booking/manage.html",
        {
            "form": form,
            "appointments": appointments,
            "searched": searched,
        },
    )


def manage_booking_detail(request, appointment_id):
    manage_email = request.session.get("manage_email")
    if not manage_email:
        messages.error(
            request,
            "Please enter your email first so we can find your bookings.",
        )
        return redirect("booking:manage_booking")

    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "clinician", "treatment"),
        pk=appointment_id,
        patient__email__iexact=manage_email,
    )
    return render(
        request,
        "booking/manage_detail.html",
        {"appointment": appointment},
    )


def cancel_booking(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "clinician", "treatment"),
        pk=appointment_id,
    )
    if not appointment.is_active_booking or appointment.status == Appointment.STATUS_ATTENDED:
        messages.error(request, "This booking cannot be cancelled.")
        return redirect("booking:manage_booking")

    if request.method == "POST":
        form = CancelBookingForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data.get("reason") or ""
            today = timezone.localdate()
            if appointment.appointment_date <= today + timedelta(days=1):
                appointment.status = Appointment.STATUS_LATE_CANCEL
            else:
                appointment.status = Appointment.STATUS_CANCELLED
            if reason:
                appointment.notes = (appointment.notes + "\n" if appointment.notes else "") + f"Cancel reason: {reason}"
            appointment.save()
            appointment.reminders.filter(status=ReminderLog.STATUS_PENDING).delete()
            send_cancellation_notice(appointment)
            messages.success(request, "Your appointment has been cancelled.")
            return redirect("booking:booking_success", appointment_id=appointment.id)
    else:
        form = CancelBookingForm()

    return render(
        request,
        "booking/cancel.html",
        {"appointment": appointment, "form": form},
    )


def start_reschedule(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if not appointment.is_active_booking or appointment.status == Appointment.STATUS_ATTENDED:
        messages.error(request, "This booking cannot be rescheduled.")
        return redirect("booking:manage_booking")

    request.session["reschedule_appointment_id"] = appointment.id
    request.session["booking_clinician_id"] = appointment.clinician_id
    return redirect("booking:select_date", clinician_id=appointment.clinician_id)


@staff_member_required(login_url="/admin/login/")
def reports(request):
    """Clinic reports page — available at /admin/reports/"""
    today = timezone.localdate()
    week_end = today + timedelta(days=7)

    upcoming = Appointment.objects.filter(
        appointment_date__gte=today,
        appointment_date__lte=week_end,
        status__in=[Appointment.STATUS_BOOKED, Appointment.STATUS_CONFIRMED],
    ).select_related("patient", "clinician", "treatment")

    recent_no_shows = Appointment.objects.filter(
        status=Appointment.STATUS_NO_SHOW,
        appointment_date__gte=today - timedelta(days=30),
    ).select_related("patient", "clinician")

    status_counts = (
        Appointment.objects.filter(appointment_date__gte=today - timedelta(days=30))
        .values("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )

    # Rough unused-slot estimate for next 7 weekdays across active clinicians
    clinicians = Clinician.objects.filter(is_active=True)
    total_slots = 0
    booked_slots = 0
    for day_offset in range(0, 10):
        day = today + timedelta(days=day_offset)
        if day.weekday() >= 5:
            continue
        if day > week_end:
            break
        for clinician in clinicians:
            day_slots = get_available_slots(clinician, day)
            # available + booked active = full day capacity conceptually
            active_booked = Appointment.objects.filter(
                clinician=clinician,
                appointment_date=day,
                status__in=[
                    Appointment.STATUS_BOOKED,
                    Appointment.STATUS_CONFIRMED,
                    Appointment.STATUS_ATTENDED,
                ],
            ).count()
            total_slots += len(day_slots) + active_booked
            booked_slots += active_booked

    unused_slots = max(total_slots - booked_slots, 0)
    reminder_stats = ReminderLog.objects.aggregate(
        pending=Count("id", filter=Q(status=ReminderLog.STATUS_PENDING)),
        sent=Count("id", filter=Q(status=ReminderLog.STATUS_SENT)),
        failed=Count("id", filter=Q(status=ReminderLog.STATUS_FAILED)),
    )

    return render(
        request,
        "booking/reports.html",
        {
            "upcoming": upcoming,
            "recent_no_shows": recent_no_shows,
            "status_counts": status_counts,
            "unused_slots": unused_slots,
            "booked_slots": booked_slots,
            "total_slots": total_slots,
            "reminder_stats": reminder_stats,
            "today": today,
            "week_end": week_end,
        },
    )


def _clear_booking_session(request):
    for key in (
        "booking_clinician_id",
        "booking_date",
        "booking_time",
        "reschedule_appointment_id",
    ):
        request.session.pop(key, None)
