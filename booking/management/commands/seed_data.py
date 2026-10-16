from django.core.management.base import BaseCommand

from booking.models import Clinician, TreatmentType


class Command(BaseCommand):
    help = "Load sample clinicians and treatments for SmileCare Dental"

    def handle(self, *args, **options):
        clinicians = [
            {
                "name": "Dr Sarah Nguyen",
                "title": "General Dentist",
                "specialty": "Check-ups and preventive care",
                "bio": "Focuses on family dentistry and routine preventive appointments.",
                "photo": "clinician-sarah.png",
            },
            {
                "name": "Dr James Patel",
                "title": "General Dentist",
                "specialty": "Fillings and restorative work",
                "bio": "Experienced in restorative treatments and same-week follow-ups.",
                "photo": "clinician-patel.png",
            },
            {
                "name": "Dr Emily Chen",
                "title": "Dental Hygienist",
                "specialty": "Cleans and gum care",
                "bio": "Supports patients with cleaning appointments and oral hygiene plans.",
                "photo": "clinician-chen.png",
            },
        ]

        treatments = [
            {"name": "Check-up", "duration_minutes": 30, "description": "Routine dental examination."},
            {"name": "Clean", "duration_minutes": 45, "description": "Professional cleaning appointment."},
            {"name": "Filling", "duration_minutes": 60, "description": "Restorative filling appointment."},
            {"name": "Follow-up", "duration_minutes": 30, "description": "Short review after treatment."},
        ]

        for data in clinicians:
            Clinician.objects.update_or_create(name=data["name"], defaults=data)

        for data in treatments:
            TreatmentType.objects.update_or_create(name=data["name"], defaults=data)

        self.stdout.write(self.style.SUCCESS("Sample data loaded."))
