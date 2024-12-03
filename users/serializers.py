from rest_framework import serializers  
from .models import User,RiderProfile,DriverProfile
from django.contrib.auth.hashers import make_password


class UserSerialer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(read_only=True) 
    # country_code = serializers.CharField(write_only=True) 
    password = serializers.CharField(write_only=True) 
    class Meta:
       model = User
       fields = ['country_code','phone','password','email','first_name','last_name','role','is_active','date_joined']


    def normalize_phone(self, phone:str, country_code='+234'):
        """
        Normalize the phone number by combining it with the country code.
        Throws an error if the phone number already includes a '+'.
        The default value for country code is +234 (Nigeria)
        """
        if phone != "":
            phone  = phone.strip()  # Remove leading/trailing spaces
            if phone.startswith("+"):
                raise ValueError("Phone number should not include a '+' sign. Provide the number without the country code.")
            
            # Combine country code and phone number
            normalized_phone = f"{country_code}{phone.lstrip('0')}"  # Remove leading zero from phone
            return normalized_phone    
        
    
    def create(self, validated_data):
        country_code = validated_data.get('country_code','+234')
        phone = validated_data.get('phone','')
        email = validated_data.get('email','')
        password = validated_data.get('password')
        first_name = validated_data.get('first_name','')
        last_name = validated_data.get('last_name','')
        role = validated_data.get('role','')
        normalized_phone = self.normalize_phone(phone=phone,country_code=country_code) # format the Phone number to international standard
        hashed_password = make_password(password) # Hash the password
        user = User.objects.create(country_code=country_code,phone=normalized_phone,password=hashed_password
        ,email=email,first_name=first_name,last_name=last_name,role=role)
        return user
    

    

class RiderProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiderProfile
        fields =[]


class DriverProfileSerializer(serializers.ModelSerializer):
    pass