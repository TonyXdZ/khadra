from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core import mail
from allauth.account.models import EmailAddress
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from users.models import Profile, City, UpgradeRequest
from users.messages import users_messages
from users.tests.test_utils import create_new_user, create_test_image, verify_email_address


UserModel = get_user_model()

# Ovveriding prod spatial data with light weigth test layers to speed up tests
@override_settings(SPATIAL_LAYER_PATHS=settings.TEST_SPATIAL_LAYER_PATHS)
class UpgradeRequestTestCase(TestCase):

    @classmethod
    def setUpTestData(self):
        call_command('load_spatial_layers', 'DZ')
        self.client_1 = Client()
        self.client_2 = Client()
        self.annaba_city = City.objects.get(name='Annaba')
        self.point_in_annaba = self.annaba_city.get_random_location_point()

    def test_upgrade_request_success(self):
        """Volunteer can successfully submit a new upgrade request."""
        volunteer = create_new_user(email='volunteer@gmail.com',
                                    username='volunteer',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        self.client_1.login(username='volunteer', password='qsdflkjlkj')

        response = self.client_1.post(reverse('upgrade-request'), {'motivation': 'im a good guy'})
        upgrade_request = UpgradeRequest.objects.filter(user=volunteer)
        self.assertTrue(upgrade_request.exists())

    def test_upgrade_request_while_having_one_on_pending(self):
        """Volunteer cannot submit a second request if a pending one already exists (403)."""
        volunteer = create_new_user(email='volunteer@gmail.com',
                                    username='volunteer',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        self.client_1.login(username='volunteer', password='qsdflkjlkj')

        response = self.client_1.post(reverse('upgrade-request'), {'motivation': 'im a good guy'})
        upgrade_request = UpgradeRequest.objects.filter(user=volunteer)
        self.assertTrue(upgrade_request.exists())

        second_response = self.client_1.post(reverse('upgrade-request'), {'motivation': 'Again !!! im a good guy'})
        self.assertEqual(second_response.status_code, 403)

    def test_upgrade_request_while_having_rejected_requests(self):
        """Volunteer can submit a new request if their previous one was rejected."""
        
        volunteer = create_new_user(email='volunteer@gmail.com',
                                    username='volunteer',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        self.client_1.login(username='volunteer', password='qsdflkjlkj')

        response = self.client_1.post(reverse('upgrade-request'), {'motivation': 'im a good guy'})
        upgrade_request = UpgradeRequest.objects.filter(user=volunteer).first()
        upgrade_request.status = 'rejected'
        upgrade_request.save()
        
        second_response = self.client_1.post(reverse('upgrade-request'), {'motivation': 'Again !!! im a good guy'})
        all_upgrade_requests = UpgradeRequest.objects.filter(user=volunteer)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(all_upgrade_requests.count(), 2)

    def test_upgrade_request_while_having_rejected_requests(self):
        """
        Volunteer can't submit a new request if their previous 
        one was approved requests (403).
        this test is just for the coverage because when the volunteer
        have approved upgrade request he automatically becomes a manager.
        """
        volunteer = create_new_user(email='volunteer@gmail.com',
                                    username='volunteer',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        self.client_1.login(username='volunteer', password='qsdflkjlkj')

        response = self.client_1.post(reverse('upgrade-request'), {'motivation': 'im a good guy'})
        upgrade_request = UpgradeRequest.objects.filter(user=volunteer).first()
        upgrade_request.status = 'approved'
        upgrade_request.save()
        
        second_response = self.client_1.post(reverse('upgrade-request'), {'motivation': 'Again !!! im a good guy'})
        all_upgrade_requests = UpgradeRequest.objects.filter(user=volunteer)
        self.assertEqual(second_response.status_code, 403)
        self.assertEqual(all_upgrade_requests.count(), 1)

    def test_upgrade_request_as_manager(self):
        """Managers cannot submit upgrade requests (403)."""
        manager = create_new_user(email='manager@gmail.com',
                                    username='manager',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        self.client_1.login(username='manager', password='qsdflkjlkj')

        response = self.client_1.post(reverse('upgrade-request'), {'motivation': 'im a good guy'})
               
        upgrade_requests = UpgradeRequest.objects.filter(user=manager).exists()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(upgrade_requests, False)
