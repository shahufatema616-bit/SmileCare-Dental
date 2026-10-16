from django.urls import path

from . import views

app_name = "booking"

urlpatterns = [
    path("", views.home, name="home"),
    path("developer/", views.developer, name="developer"),
    path("book/", views.select_clinician, name="select_clinician"),
    path("book/clinician/<int:clinician_id>/", views.select_date, name="select_date"),
    path(
        "book/clinician/<int:clinician_id>/date/<str:date_str>/",
        views.select_time,
        name="select_time",
    ),
    path(
        "book/clinician/<int:clinician_id>/date/<str:date_str>/time/<str:time_str>/",
        views.set_time_and_confirm,
        name="set_time",
    ),
    path("book/confirm/", views.confirm_booking, name="confirm_booking"),
    path("book/success/<int:appointment_id>/", views.booking_success, name="booking_success"),
    path("manage/", views.manage_booking, name="manage_booking"),
    path(
        "manage/booking/<int:appointment_id>/",
        views.manage_booking_detail,
        name="manage_booking_detail",
    ),
    path("manage/<int:appointment_id>/cancel/", views.cancel_booking, name="cancel_booking"),
    path(
        "manage/<int:appointment_id>/reschedule/",
        views.start_reschedule,
        name="start_reschedule",
    ),
]
