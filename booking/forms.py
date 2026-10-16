from django import forms

from .models import Appointment, Patient, TreatmentType


class PatientBookingForm(forms.ModelForm):
    treatment = forms.ModelChoiceField(
        queryset=TreatmentType.objects.all(),
        empty_label="Select appointment type",
    )

    class Meta:
        model = Patient
        fields = ["first_name", "last_name", "email", "phone"]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@email.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "04xx xxx xxx"}),
        }


class ManageBookingForm(forms.Form):
    email = forms.EmailField(
        label="Email used for booking",
        widget=forms.EmailInput(attrs={"placeholder": "you@email.com"}),
        error_messages={
            "required": "Please enter the email address you used when booking.",
            "invalid": "Please enter a valid email address.",
        },
    )


class CancelBookingForm(forms.Form):
    reason = forms.CharField(
        required=False,
        label="Reason (optional)",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Optional reason"}),
    )
