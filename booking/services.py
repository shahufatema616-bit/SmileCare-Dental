from datetime import date, datetime, time, timedelta

from django.utils import timezone

from .models import Appointment

WORK_START = time(9, 0)
WORK_END = time(17, 0)
SLOT_MINUTES = 30


def upcoming_dates(days=14):
    today = timezone.localdate()
    dates = []
    current = today
    while len(dates) < days:
        if current.weekday() < 5:
            dates.append(current)
        current += timedelta(days=1)
    return dates


def generate_time_slots():
    slots = []
    current = datetime.combine(date.today(), WORK_START)
    end = datetime.combine(date.today(), WORK_END)
    while current < end:
        slots.append(current.time())
        current += timedelta(minutes=SLOT_MINUTES)
    return slots


def get_available_slots(clinician, appointment_date, exclude_appointment_id=None):
    qs = Appointment.objects.filter(
        clinician=clinician,
        appointment_date=appointment_date,
        status__in=[
            Appointment.STATUS_BOOKED,
            Appointment.STATUS_CONFIRMED,
            Appointment.STATUS_ATTENDED,
        ],
    )
    if exclude_appointment_id:
        qs = qs.exclude(pk=exclude_appointment_id)
    booked = set(qs.values_list("start_time", flat=True))
    return [slot for slot in generate_time_slots() if slot not in booked]


def slot_end_time(start_time, duration_minutes):
    start = datetime.combine(date.today(), start_time)
    end = start + timedelta(minutes=duration_minutes)
    return end.time()
