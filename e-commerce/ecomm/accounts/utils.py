import random
import string
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    digits = string.digits
    otp = ''.join(random.choice(digits) for i in range(6))  # 6-digit OTP
    return otp

def send_otp_email(email, otp):
    subject = 'Your OTP for Password Reset'
    message = f'Your OTP for password reset is {otp}.'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    try:
        send_mail(subject, message, email_from, recipient_list)
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")
    