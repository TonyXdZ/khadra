from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from users.models import Profile

UserModel = get_user_model()

def create_new_user(email, username, password, phone_number, bio, account_type='volunteer'):
    """
    Helper function to create a new user with a profile
    """
    user = UserModel.objects.create_user(username=username, password=password)
    email = EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    Profile.objects.create(user=user, phone_number=phone_number, account_type=account_type)
    return user