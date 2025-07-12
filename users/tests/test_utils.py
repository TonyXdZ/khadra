from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from users.models import Profile, Country

UserModel = get_user_model()

def create_new_user(email, username, password, phone_number, bio, account_type='volunteer', city=None, geo_location=None):
    """
    Helper function to create a new user with a profile
    """
    user = UserModel.objects.create_user(username=username, password=password)
    email = EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    algeria = Country.objects.get(iso2='DZ')
    Profile.objects.create(user=user, 
                            phone_number=phone_number,
                            bio=bio,
                            account_type=account_type,
                            country=algeria,
                            city=city,
                            geo_location=geo_location)
    return user


def create_test_image(name='test.jpg', ext='JPEG', size=(100, 100), color=(255, 0, 0)):
    """
    Helper function that returns an image file that will be used in tests
    """
    file = BytesIO()
    image = Image.new('RGB', size, color)
    image.save(file, ext)
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type='image/jpeg')


def verify_email_address(email):
    """
    Marks the given email address as verified and primary for the associated user.

    Parameters:
        email (str): The email address to verify.

    Raises:
        EmailAddress.DoesNotExist: If no EmailAddress object with the given email is found.
    """
    email_address = EmailAddress.objects.get(email=email)
    email_address.verified = True
    email_address.primary = True
    email_address.save()