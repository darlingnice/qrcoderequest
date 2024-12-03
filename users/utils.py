import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import BadHeaderError
from smtplib import SMTPException
import socket
from django.conf import settings

class EmailSender:
    def __init__(self, subject, from_email=settings.EMAIL_HOST_USER):
        self.subject = subject
        self.from_email = from_email

    def send_email_async(self, html_content, text_content, to):
        try:
            email = EmailMultiAlternatives(self.subject, text_content, self.from_email, [to])
            email.attach_alternative(html_content, "text/html")
            email.send()
        except BadHeaderError:
            print("Invalid header found in the email.")
        except SMTPException as e:
            print(f"SMTP error occurred: {e}")
        except socket.gaierror:
            print("Network error: Unable to connect to the mail server.")
        except TimeoutError:
            print("Timeout error: The connection to the mail server timed out.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        except ConnectionError as e:  
            print(f"Connection error occurred: {e}")  

    def _start_email_thread(self, html_content, text_content, to):
        email_thread = threading.Thread(target=self.send_email_async, args=(html_content, text_content, to))
        email_thread.start()

    def send_confirm_email(self,scheme,host,endpoint,email,first_name,user_pk,token):
        try:
                to = email
                html_content = render_to_string('confirm_email.html', {
                    'scheme': scheme,
                    'host':host,
                    'endpoint':endpoint,
                    'first_name':first_name,
                    'uid':user_pk,
                    'token': token
                })
                text_content = strip_tags(html_content)
                self._start_email_thread(html_content, text_content, to)
        except BadHeaderError:
            ("Invalid header found in the email.")
        except SMTPException as e:
            return(f"SMTP error occurred while sending the forgot password email: {e}")
        except socket.gaierror:
            return("Network error: Unable to connect to the mail server.")
        except TimeoutError:
            return("Timeout error: The connection to the mail server timed out.")
        except ConnectionRefusedError:
            return("The connection was refused by the mail server.")
        except socket.error as e:
            return(f"Socket error: {e}")
        except Exception as e:
                return(f"An unexpected error occurred: {e}")
         

    def send_otp_email(self,email, first_name, otp_code,time):
        to = email
        html_content = render_to_string('otp_email_template.html', {
            'email': email,
            'first_name': first_name,
            'otp_code': otp_code,
            'time': f"{time} seconds"
        })
        text_content = strip_tags(html_content)
        self._start_email_thread(html_content, text_content, to)

   

# Usage Example
# email_sender = EmailSender(subject='Reset Your Password')
# email_sender.send_forgot_password_link(request, email, user_id, first_name, token)




from django.db import transaction

class TaskWithOnCommit:
    def __init__(self, task):
        """
        Initializes the wrapper class with a Celery task.
        :param task: A Celery task function.
        """
        self.task = task

    def delay_on_commit(self, *args, **kwargs):
        """
        Schedules the task to run after the transaction is committed.
        :param args: Arguments to be passed to the task.
        :param kwargs: Keyword arguments to be passed to the task.
        """
        # Use Django's transaction.on_commit to delay the task execution
        transaction.on_commit(lambda: self.task.delay(*args, **kwargs))
