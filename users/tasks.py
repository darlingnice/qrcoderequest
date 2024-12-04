from celery import shared_task
from .utils import TaskWithOnCommit
from .models import User
from .utils import EmailSender
# from celery.exceptions import MaxRetriesExceededError

@shared_task
def send_confirmation_email_to_user(scheme,host,endpoint,user_pk):
    user = User.objects.get(pk=user_pk) 
    email_sender_obj = EmailSender('RideAPP Email Confirmation Message ')
    try:
        email_sender_obj.send_confirm_email(scheme=scheme,host=host,endpoint=endpoint,email=user.email, first_name=user.first_name,user_pk=user_pk,token='838i3bb74774')#for testing change token later
        return f"Email sent to {user.email}"
    except Exception as exc:
        return f"Failed to send email to {user.email}. Exception occured."
          
send_confirmation_email_to_user = TaskWithOnCommit(send_confirmation_email_to_user)



@shared_task
def send_email_on_QRCODE_scan(email):
    email_sender_obj = EmailSender('QRCCode Scanned  Message ')
    try:
        email_sender_obj.send_meessage_for_QRCode_Scan(email=email)
        return f"Email sent to {email}"
    except Exception as exc:
        return f"Failed to send email to {email}. Exception occured."
          
send_email_on_QRCODE_scan = TaskWithOnCommit(send_email_on_QRCODE_scan)



