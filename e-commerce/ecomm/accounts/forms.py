import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model,authenticate
from .models import Account
from django.core.validators import RegexValidator
from wallet.models import Referral
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm





User = get_user_model()

class AdminLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user or not user.is_staff:
                raise forms.ValidationError("Incorrect admin email and password")
        return cleaned_data


class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat Password', widget=forms.PasswordInput)
    phone_number = forms.CharField(
        validators=[RegexValidator(regex=r'^\d{10}$', message="Phone number must be a 10-digit number.")]
    )

    referral_code = forms.CharField(required=False, label='Referral Code')


    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number must not contain characters or symbols.")
        if len(phone_number) != 10:
            raise forms.ValidationError("Phone number must be a 10-digit number.")
        return phone_number

    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'\d', password):
            raise forms.ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError("Password must contain at least one symbol.")
        
        return password

    def __init__(self,*args,**kwargs):
        super(SignupForm,self).__init__(*args,**kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter Last Name'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Enter Phone Number'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email Address'
        self.fields['password'].widget.attrs['placeholder'] = 'Enter Password'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if Account.objects.filter(username=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
    
    def clean_referral_code(self):
        referral_code = self.cleaned_data.get('referral_code')
        if referral_code:
            if not Referral.objects.filter(referral_code=referral_code).exists():
                raise forms.ValidationError("Invalid referral code.")
        return referral_code

    def save(self, commit=True):
        user = super(SignupForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
     

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError("Wrong credentials.")
            if not user.is_active:
                raise forms.ValidationError("Account is inactive.")
        return cleaned_data




class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(max_length=254)

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6)
    scenario = forms.CharField(widget=forms.HiddenInput(), required=False)

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label='New password:', widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='Repeat password:', widget=forms.PasswordInput)


