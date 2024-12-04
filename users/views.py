from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny
from .serializers import UserSerialer,RiderProfileSerializer,DriverProfileSerializer
from django.db.utils import IntegrityError
from django.contrib.auth import authenticate,login
from .tasks import send_confirmation_email_to_user,send_email_on_QRCODE_scan

# Rider registration logic 
@api_view(['POST'])
@permission_classes([AllowAny])
def register_rider(request):
    rider_data = request.data
    serializer = UserSerialer(data=rider_data)
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    endpoint = 'confirm-email'
    try:
        if serializer.is_valid():
            user = serializer.save()
            # send an email confirmation message process to celery 
            send_confirmation_email_to_user.delay_on_commit(scheme,host,endpoint,user.pk)
            return Response(data={'message':'Rider account created'},status=status.HTTP_201_CREATED)  
        return Response(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError as e:  
          # Handle database integrity issues (e.g., unique constraint violations)
        error_message = str(e)
        print(error_message)
        if 'UNIQUE constraint failed' in error_message:
            return Response(
                data={'errors': 'A user with this email or phone number already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            data={'errors': 'Database integrity error occurred.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    except Exception as e:
        # Catch unexpected exceptions
        return Response(
            data={'errors': f'An unexpected error occurred: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Driver registration logic 
@api_view(['POST'])
@permission_classes([AllowAny])
def register_driver(request):
    return Response(data={},status=status.HTTP_200_OK)


# Login rider logic 
@api_view(['POST'])
@permission_classes([AllowAny])
def login_rider(request):
    email = request.data.get('email')
    phone = request.data.get('phone','')
    password = request.data.get('password')
    authentication_type = email
    if phone  and not email:
        authentication_type = phone
    user = authenticate(request,username=authentication_type,password=password)
    if user is not None:
        
        login(request,user)
    return Response(data={"user":str(user)},status=status.HTTP_200_OK)

# Login driver logic
def login_driver(request):
    return Response(status=status.HTTP_200_OK)

import pyqrcode
import png
from pyqrcode import QRCode

@api_view(["GET"])
@permission_classes([AllowAny])
def generate_code(request):
    email:str = request.GET.get('email')
    # Data to encode in the QR code
    data = f"http://lyntonjay.pythonanywhere.com/auth/email-on-scan/?email={email}"

    # Generate QR code
    qr_code = pyqrcode.create(data)

    # Save the QR code as a PNG file
    qr_code.png(f"{email.split('@')[0]}qrcode.png", scale=6)

    # Save the QR code as a string (text version)
    print(qr_code.terminal(quiet_zone=1))

    print(f"QR Code saved as '{email.split('@')[0]}qrcode.png'")
    # with open(r'/home/lyntonjay/dev/Microservices_Projects/ride_app/user_service/lyntontronicsqrcode.png') as file:
    #     qr_code_image = file.read()
    # return render(request,'tt.html')

    return Response(data={'data':f'QR code generated for {email}'},status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def send_message_on_scan(request): 
    email:str = request.GET.get('email') 
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    print(f'QRC for {email}')
    send_email_on_QRCODE_scan.delay_on_commit(email=email)
    return Response(data={'success':f'You scanned the QR code. An email has been sent to {email}'},status=status.HTTP_200_OK)



# Implement user authentication with email/phone login, profile management, and validation

# - Added user registration and login via email or phone
# - Implemented password hashing and authentication logic
# - Created user profile management with role-based access (Rider/Driver)
# - Added validation for user input (phone normalization, email uniqueness)
# - Implemented custom user manager for creating users and superusers

# #user-service #authentication #profile-management


# https://www.youtube.com/watch?v=b2kdhkUXI2U celery video