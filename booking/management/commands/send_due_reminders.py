from django.core.management.base import BaseCommand

from booking.notifications import process_due_reminders


class Command(BaseCommand):
    help = "Send due appointment reminders (email + simulated SMS log)"

    def handle(self, *args, **options):
        count = process_due_reminders()
        self.stdout.write(self.style.SUCCESS(f"Processed {count} due reminder(s)."))
