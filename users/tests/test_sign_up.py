from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from django.test import Client, TestCase
from django.urls import reverse
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

class UserSignUpTestCase(TestCase):

    @classmethod
    def setUpTestData(self):

        self.client_1 = Client()
        self.client_2 = Client()

    def test_user_with_profile_get_403_forbidden_when_trying_access_create_profile_page(self):
        """
        Creat a user with profile and when he try to create another profile
        by accessing the link for profile creation the response should be 403 forbidden
        """
        some_dude = create_new_user(email='somedude@gmail.com',
                                    username='some_dude',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio')

        #login the new user
        login_response = self.client_1.post(reverse('account_login'), {'login': 'some_dude', 'password': 'qsdflkjlkj'})

        #get profile create page
        get_response = self.client_1.get(reverse('create-profile'))

        self.assertEqual( get_response.status_code, 403)


    def test_full_sign_up_with_profile_creation(self):
        """
        Signup and create profile normally
        """
        sign_up_response = self.client_1.post( reverse('account_signup'),
                                {
                                 'username':'charoufa', 
                                 'email': 'achref@gmail.com',
                                 'password1': 'qsdf654654',
                                 'password2': 'qsdf654654',
                                }, 
                             )
        #Verify email address
        email_address = EmailAddress.objects.get(email='achref@gmail.com')
        email_address.verified = True
        email_address.primary = True
        email_address.save()

        #Login the user since he logged out unil email is verified
        self.client_1.post(reverse('account_login'), {'login': 'charoufa', 'password': 'qsdf654654'})
        profile_response = self.client_1.post( reverse('create-profile'), 
                                        {'account_type': 'volunteer',
                                        'bio': 'ssup', 
                                        'phone_number': '0666778855'})

        new_user = UserModel.objects.get(username='charoufa')

        self.assertEqual( profile_response.status_code , 302)
        self.assertEqual( new_user.username , 'charoufa')
        self.assertEqual( hasattr(new_user, 'profile'), True)
        self.assertEqual( new_user.profile.bio, 'ssup')
        self.assertEqual( new_user.profile.phone_number, '+213666778855')

    def test_redirect_when_profile_not_created(self):
        """
        Users without a profile are redirected from 'profile'
        to 'create_profile' page.
        """
        sign_up_response = self.client_1.post( reverse('account_signup'),
                                {
                                 'username':'redirected_user', 
                                 'email': 'redirected_user@gmail.com',
                                 'password1': 'qsdf654654',
                                 'password2': 'qsdf654654',
                                }, 
                             )
        #Verify email address
        email_address = EmailAddress.objects.get(email='redirected_user@gmail.com')
        email_address.verified = True
        email_address.primary = True
        email_address.save()

        #Login the user since he logged out unil email is verified
        self.client_1.post(reverse('account_login'), {'login': 'redirected_user', 'password': 'qsdf654654'})
        
        #request my profile without a profile
        my_profile_response = self.client_1.get(reverse('profile'))
        
        self.assertRedirects(
            my_profile_response,
            reverse('create-profile'),
            status_code=302,
            fetch_redirect_response=False
        )

    def test_users_with_profile_can_access_profile_page(self):
        """
        Signup and create profile normally and assert
        users can access profile page
        """
        sign_up_response = self.client_1.post( reverse('account_signup'),
                                {
                                 'username':'no_redirect_user', 
                                 'email': 'no_redirect_user@gmail.com',
                                 'password1': 'qsdf654654',
                                 'password2': 'qsdf654654',
                                }, 
                             )
        #Verify email address
        email_address = EmailAddress.objects.get(email='no_redirect_user@gmail.com')
        email_address.verified = True
        email_address.primary = True
        email_address.save()

        #Login the user since he logged out unil email is verified
        self.client_1.post(reverse('account_login'), {'login': 'no_redirect_user', 'password': 'qsdf654654'})
        profile_response = self.client_1.post( reverse('create-profile'), 
                                        {'account_type': 'volunteer',
                                        'bio': 'ssup', 
                                        'phone_number': '0666778855'})

        get_profile_response = self.client_1.get(reverse('profile'))

        self.assertEqual( get_profile_response.status_code , 200)