from django.urls import path
from . import views 

urlpatterns = [
    path('register/rider/',views.register_rider),
    path('register/driver/',views.register_driver),
    path('login/rider/',views.login_rider),
    path('login/driver/',views.login_driver),
    path('email-on-scan/',views.send_message_on_scan,name='scan'),
    path('generate-code/',views.generate_code,name='generate-qrcode')
]
