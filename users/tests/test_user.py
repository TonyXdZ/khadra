from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from allauth.account.models import EmailAddress
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from users.models import Profile, City
from users.tests.test_utils import create_new_user, create_test_image, verify_email_address


UserModel = get_user_model()

# Ovveriding prod spatial data with light weigth test layers to speed up tests
@override_settings(SPATIAL_LAYER_PATHS=settings.TEST_SPATIAL_LAYER_PATHS)
class UserTestCase(TestCase):

    @classmethod
    def setUpTestData(self):
        call_command('load_spatial_layers', 'DZ')
        self.client_1 = Client()
        self.client_2 = Client()
        self.annaba_city = City.objects.get(name='Annaba')
        self.point_in_annaba = self.annaba_city.get_random_location_point()

    def test_user_with_profile_get_403_forbidden_when_trying_access_create_profile_page(self):
        """
        Creat a user with profile and when he try to create another profile
        by accessing the link for profile creation the response should be 403 forbidden
        """
        some_dude = create_new_user(email='somedude@gmail.com',
                                    username='some_dude',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        #login the new user
        login_response = self.client_1.post(reverse('account_login'), {'login': 'some_dude', 'password': 'qsdflkjlkj'})

        #get profile create page
        get_response = self.client_1.get(reverse('create-profile'))

        self.assertEqual( get_response.status_code, 403)


    def test_full_sign_up_with_profile_creation(self):
        """
        Signup and create profile normally without profile picture
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
        verify_email_address('achref@gmail.com')

        #Login the user since he logged out unil email is verified
        self.client_1.post(reverse('account_login'), {'login': 'charoufa', 'password': 'qsdf654654'})
        profile_response = self.client_1.post( reverse('create-profile'), 
                                        {'account_type': 'volunteer',
                                        'bio': 'ssup', 
                                        'phone_number': '0666778855',
                                        'city': str(self.annaba_city.pk),
                                        })

        new_user = UserModel.objects.get(username='charoufa')

        self.assertEqual( profile_response.status_code , 302)
        self.assertEqual( new_user.username , 'charoufa')
        self.assertEqual( hasattr(new_user, 'profile'), True)
        self.assertEqual( new_user.profile.bio, 'ssup')
        self.assertEqual( new_user.profile.phone_number, '+213666778855')
        self.assertEqual( new_user.profile.city, self.annaba_city)

    def test_full_sign_up_with_profile_creation_and_profile_pic(self):
        """
        Signup and create profile normally WITH profile picture
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
        verify_email_address('achref@gmail.com')

        test_image_file = create_test_image()

        #Login the user since he logged out unil email is verified
        self.client_1.post(reverse('account_login'), {'login': 'charoufa', 'password': 'qsdf654654'})
        profile_response = self.client_1.post( reverse('create-profile'), 
                                        {'profile_pic': test_image_file,
                                        'account_type': 'volunteer',
                                        'bio': 'ssup', 
                                        'phone_number': '0666778855',
                                        'city': str(self.annaba_city.pk),
                                        })

        new_user = UserModel.objects.get(username='charoufa')

        self.assertEqual( profile_response.status_code , 302)
        self.assertEqual( new_user.username , 'charoufa')
        self.assertEqual( hasattr(new_user, 'profile'), True)
        self.assertEqual( new_user.profile.bio, 'ssup')
        self.assertEqual( new_user.profile.phone_number, '+213666778855')
        self.assertEqual( new_user.profile.city, self.annaba_city)
        self.assertNotEqual( new_user.profile.profile_pic, '' )

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
        verify_email_address('redirected_user@gmail.com')

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
        verify_email_address('no_redirect_user@gmail.com')

        #Login the user since he logged out unil email is verified
        self.client_1.post(reverse('account_login'), {'login': 'no_redirect_user', 'password': 'qsdf654654'})
        profile_response = self.client_1.post( reverse('create-profile'), 
                                        {'account_type': 'volunteer',
                                        'bio': 'ssup', 
                                        'phone_number': '0666778855',
                                        'city': str(self.annaba_city.pk),
                                        })

        get_profile_response = self.client_1.get(reverse('profile'))

        self.assertEqual( get_profile_response.status_code , 200)

    def test_update_user_profile(self):
        """
        Signup and create profile normally WITH profile picture
        """
        sign_up_response = self.client_1.post( reverse('account_signup'),
                                {
                                 'username':'tobe_updated', 
                                 'email': 'tobe_updated@gmail.com',
                                 'password1': 'qsdf654654',
                                 'password2': 'qsdf654654',
                                }, 
                             )
        #Verify email address
        verify_email_address('tobe_updated@gmail.com')

        test_image_file = create_test_image()

        #Login the user since he logged out unil email is verified
        self.client_1.post(reverse('account_login'), {'login': 'tobe_updated', 'password': 'qsdf654654'})
        profile_response = self.client_1.post( reverse('create-profile'), 
                                        {'profile_pic': test_image_file,
                                        'account_type': 'volunteer',
                                        'bio': 'ssup', 
                                        'phone_number': '0666778855',
                                        'city': str(self.annaba_city.pk),
                                        })


        #Profile update part
        profile_response = self.client_1.post( reverse('profile-update'), 
                                        {'profile_pic-clear': 'on',#clears the profile pic field
                                        'account_type': 'manager',
                                        'bio': 'new bio', 
                                        'phone_number': '0666778866',
                                        'username': 'already_updated',
                                        'first_name': 'Happy',
                                        'last_name': 'User',
                                        })
        updated_user = UserModel.objects.get(username='already_updated')

        self.assertEqual( profile_response.status_code , 302)
        self.assertEqual( updated_user.username , 'already_updated')
        self.assertEqual( updated_user.first_name , 'Happy')
        self.assertEqual( updated_user.last_name , 'User')
        self.assertEqual( updated_user.profile.bio, 'new bio')
        self.assertEqual( updated_user.profile.account_type, 'manager')#Might change in the future
        self.assertEqual( updated_user.profile.phone_number, '+213666778866')
        self.assertEqual( updated_user.profile.profile_pic, '' )