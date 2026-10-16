from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import ReminderLog


def appointment_datetime(appointment):
    return timezone.make_aware(
        datetime.combine(appointment.appointment_date, appointment.start_time)
    )


def send_email_message(subject, body, to_email, appointment, scheduled_for=None, mark_sent=True):
    status = ReminderLog.STATUS_SENT if mark_sent else ReminderLog.STATUS_PENDING
    sent_at = timezone.now() if mark_sent else None

    if mark_sent:
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [to_email],
                fail_silently=False,
            )
            # Extra clear marker for console/demo terminals
            print("\n" + "=" * 60)
            print("SMILECARE EMAIL SENT")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print("=" * 60 + "\n")
        except Exception as exc:
            status = ReminderLog.STATUS_FAILED
            sent_at = None
            print(f"\n[SmileCare] EMAIL FAILED to {to_email}: {exc}\n")
            ReminderLog.objects.create(
                appointment=appointment,
                channel=ReminderLog.CHANNEL_EMAIL,
                message=body,
                status=status,
                scheduled_for=scheduled_for,
                sent_at=sent_at,
            )
            return False

    ReminderLog.objects.create(
        appointment=appointment,
        channel=ReminderLog.CHANNEL_EMAIL,
        message=body,
        status=status,
        scheduled_for=scheduled_for,
        sent_at=sent_at,
    )
    return True


def log_simulated_sms(appointment, message, scheduled_for=None, mark_sent=True):
    ReminderLog.objects.create(
        appointment=appointment,
        channel=ReminderLog.CHANNEL_SMS,
        message=message,
        status=ReminderLog.STATUS_SENT if mark_sent else ReminderLog.STATUS_PENDING,
        scheduled_for=scheduled_for,
        sent_at=timezone.now() if mark_sent else None,
    )


def send_confirmation(appointment):
    subject = "SmileCare Dental — appointment confirmed"
    body = (
        f"Hi {appointment.patient.first_name},\n\n"
        f"Your appointment is confirmed.\n\n"
        f"Reference: #{appointment.id}\n"
        f"Clinician: {appointment.clinician.name}\n"
        f"Treatment: {appointment.treatment.name}\n"
        f"Date: {appointment.appointment_date.strftime('%A, %d %B %Y')}\n"
        f"Time: {appointment.start_time.strftime('%I:%M %p')}\n\n"
        f"Need to change it? Open Manage booking on our website and enter this email: "
        f"{appointment.patient.email}\n\n"
        f"Thank you,\nSmileCare Dental"
    )
    send_email_message(subject, body, appointment.patient.email, appointment, mark_sent=True)
    log_simulated_sms(
        appointment,
        (
            f"SmileCare: Confirmed {appointment.appointment_date} at "
            f"{appointment.start_time.strftime('%I:%M %p')} with {appointment.clinician.name}. "
            f"Ref #{appointment.id}"
        ),
        mark_sent=True,
    )
    schedule_upcoming_reminders(appointment)


def schedule_upcoming_reminders(appointment):
    appt_dt = appointment_datetime(appointment)
    now = timezone.now()

    reminder_points = [
        (appt_dt - timedelta(hours=48), "48-hour"),
        (appt_dt - timedelta(hours=2), "2-hour"),
    ]

    for when, label in reminder_points:
        if when <= now:
            continue

        email_body = (
            f"Hi {appointment.patient.first_name},\n\n"
            f"This is your {label} reminder for your SmileCare Dental appointment.\n\n"
            f"Clinician: {appointment.clinician.name}\n"
            f"Date: {appointment.appointment_date.strftime('%A, %d %B %Y')}\n"
            f"Time: {appointment.start_time.strftime('%I:%M %p')}\n"
            f"Reference: #{appointment.id}\n\n"
            f"See you soon,\nSmileCare Dental"
        )
        ReminderLog.objects.create(
            appointment=appointment,
            channel=ReminderLog.CHANNEL_EMAIL,
            message=email_body,
            status=ReminderLog.STATUS_PENDING,
            scheduled_for=when,
        )
        ReminderLog.objects.create(
            appointment=appointment,
            channel=ReminderLog.CHANNEL_SMS,
            message=(
                f"SmileCare reminder ({label}): {appointment.appointment_date} "
                f"at {appointment.start_time.strftime('%I:%M %p')} with "
                f"{appointment.clinician.name}. Ref #{appointment.id}"
            ),
            status=ReminderLog.STATUS_PENDING,
            scheduled_for=when,
        )


def send_cancellation_notice(appointment):
    subject = "SmileCare Dental — appointment cancelled"
    body = (
        f"Hi {appointment.patient.first_name},\n\n"
        f"Your appointment (reference #{appointment.id}) has been cancelled.\n\n"
        f"Previous details:\n"
        f"Clinician: {appointment.clinician.name}\n"
        f"Date: {appointment.appointment_date.strftime('%A, %d %B %Y')}\n"
        f"Time: {appointment.start_time.strftime('%I:%M %p')}\n\n"
        f"You can book a new appointment anytime on our website.\n\n"
        f"SmileCare Dental"
    )
    send_email_message(subject, body, appointment.patient.email, appointment, mark_sent=True)
    log_simulated_sms(
        appointment,
        f"SmileCare: Appointment #{appointment.id} cancelled.",
        mark_sent=True,
    )


def send_reschedule_notice(appointment, old_date, old_time):
    subject = "SmileCare Dental — appointment rescheduled"
    body = (
        f"Hi {appointment.patient.first_name},\n\n"
        f"Your appointment (reference #{appointment.id}) has been rescheduled.\n\n"
        f"Previous: {old_date.strftime('%A, %d %B %Y')} at {old_time.strftime('%I:%M %p')}\n"
        f"New: {appointment.appointment_date.strftime('%A, %d %B %Y')} "
        f"at {appointment.start_time.strftime('%I:%M %p')}\n"
        f"Clinician: {appointment.clinician.name}\n\n"
        f"SmileCare Dental"
    )
    send_email_message(subject, body, appointment.patient.email, appointment, mark_sent=True)
    log_simulated_sms(
        appointment,
        (
            f"SmileCare: Rescheduled #{appointment.id} to "
            f"{appointment.appointment_date} {appointment.start_time.strftime('%I:%M %p')}."
        ),
        mark_sent=True,
    )
    # Clear old pending reminders and schedule new ones
    appointment.reminders.filter(status=ReminderLog.STATUS_PENDING).delete()
    schedule_upcoming_reminders(appointment)


def process_due_reminders():
    now = timezone.now()
    due = ReminderLog.objects.filter(
        status=ReminderLog.STATUS_PENDING,
        scheduled_for__lte=now,
    ).select_related("appointment", "appointment__patient", "appointment__clinician")

    sent_count = 0
    for reminder in due:
        appt = reminder.appointment
        if appt.status in (appt.STATUS_CANCELLED, appt.STATUS_LATE_CANCEL):
            reminder.status = ReminderLog.STATUS_FAILED
            reminder.message = f"[Skipped - appointment cancelled]\n{reminder.message}"
            reminder.save(update_fields=["status", "message"])
            continue

        if reminder.channel == ReminderLog.CHANNEL_EMAIL:
            try:
                send_mail(
                    "SmileCare Dental — appointment reminder",
                    reminder.message,
                    settings.DEFAULT_FROM_EMAIL,
                    [appt.patient.email],
                    fail_silently=False,
                )
                reminder.status = ReminderLog.STATUS_SENT
                reminder.sent_at = now
            except Exception:
                reminder.status = ReminderLog.STATUS_FAILED
        else:
            # Simulated SMS: mark as sent and keep in log for demo
            reminder.status = ReminderLog.STATUS_SENT
            reminder.sent_at = now

        reminder.save()
        sent_count += 1

    return sent_count
