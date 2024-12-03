from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class EmailOrPhoneBackend(BaseBackend):
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Ensure username and password are provided
        if not username or not password:
            logger.debug("Username or password not provided.")
            return None

        # Fallback to ModelBackend for admin login
        if request and request.path == '/admin/login/':
            logger.debug("Falling back to ModelBackend for admin login.")
            return None  # Pass control to the next backend

        # Attempt to find the user by email or phone
        try:
            user = User.objects.get(Q(email=username) | Q(phone=username))
        except User.MultipleObjectsReturned:
            logger.warning("Multiple users found with the same email or phone.")
            return None
        except User.DoesNotExist:
            logger.debug("User not found.")
            return None

        # Validate the password and check user status
        if user.check_password(password) and self.user_can_authenticate(user):
            logger.debug(f"User '{username}' authenticated successfully.")
            return user

        logger.debug(f"Authentication failed for user '{username}'. Incorrect password or inactive account.")
        return None

    def user_can_authenticate(self, user):
        """Check if the user is active and eligible for authentication."""
        return user.is_active
