from django.apps import AppConfig


class BookingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "booking"

    def ready(self):
        from django.contrib import admin

        admin.site.site_header = "SmileCare Dental"
        admin.site.site_title = "SmileCare Dental"
        admin.site.index_title = "Clinic management portal"
