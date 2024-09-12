# user/forms.py
from django import forms
from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['first_name','last_name','phone_number','street_address', 'city', 'state', 'country', 'postal_code', 'is_default','email']
