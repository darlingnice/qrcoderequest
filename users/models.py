from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager
from time import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, phone, password=None, **extra_fields):
        """
        Create and return a regular user with phone and password.
        """
        if not email and not   phone:
            raise ValueError("Either email or password must be set")
        if not password:
            raise ValueError("You must provide a password")
        phone = self.normalize_phone(phone,extra_fields.get('country_code','+234'))      
        user = self.model(email=self.normalize_email(email), phone=phone,country_code=extra_fields.get('country_code', '+234'),**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self,  email=None, phone=None, password=None, **extra_fields):
        if not email and not  phone:
            raise ValueError('Either email or  phone must be set for admin users')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active',True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email,phone, password, **extra_fields)

    
    def normalize_phone(self, phone:str=None, country_code='+234'):

        """
        Normalize the phone number by combining it with the country code.
        Throws an error if the phone number already includes a '+'.
        The default value for country code is +234 (Nigeria)
        """
        if phone is not None:
            phone  = phone.strip()  # Remove leading/trailing spaces
            if phone  is not None and phone.startswith("+"):
                raise ValueError("Phone number should not include a '+' sign. Provide the number without the country code.")
            
            # Combine country code and phone number
            normalized_phone = f"{country_code}{phone.lstrip('0')}"  # Remove leading zero from phone
            return normalized_phone



class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("RIDER","Rider"),
        ("DRIVER","Driver")
    )
    country_code = models.CharField(max_length=15,null=True,blank=True,default='+234') 
    email = models.EmailField(null=True,blank=True,unique=True) # Email or Phone can be  the unique identifier
    phone = models.CharField(max_length=20, unique=True,null=True,blank=True)  
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    role = models.CharField(max_length=10,choices=ROLE_CHOICES) # The role of the user , Rider or Driver

    # Flags for account status
    is_active = models.BooleanField(default=False) # Inactive untill the user has verified either their email or  phone number
    is_staff = models.BooleanField(default=False) 
    is_superuser = models.BooleanField(default=False) 
    
    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)

    # Set phone as the USERNAME_FIELD
    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = [] 

    objects = UserManager()

    def __str__(self):
        if self.email:
            return self.email
        if self.phone:
            return self.phone
        return "User without phone or email" #although not possible


class RiderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_profile')
    favorite_destinations = models.JSONField(blank=True, null=True) # Latitude and Longitude  values

class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    vehicle_details = models.JSONField(blank=True, null=True)
    license_number = models.CharField(max_length=50)
    rating = models.FloatField(default=0.0)
