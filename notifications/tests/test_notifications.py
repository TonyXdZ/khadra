from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from users.models import Profile, City
from users.tests.test_utils import create_new_user
from users.messages import users_messages
from core.tests.test_utils import create_initiative, create_multiple_initiative_reviews
from core.tasks import evaluate_initiative_reviews_task
from notifications.models import Notification

UserModel = get_user_model()

# Ovveriding prod spatial data with light weigth test layers to speed up tests
@override_settings(SPATIAL_LAYER_PATHS=settings.TEST_SPATIAL_LAYER_PATHS)
class NotificationsTestCase(TestCase):
    @classmethod
    def setUpTestData(self):
        call_command('load_spatial_layers', 'DZ')
        self.annaba_city = City.objects.get(name='Annaba')
        self.point_in_annaba = self.annaba_city.get_random_location_point()
        self.initiative_creator = create_new_user(email='manager_user@gmail.com',
                                    username='manager_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

    def test_notification_created_on_initiative_created(self):
        """
        Tests that a notification is created and sent to all managers (except the creator)
        when a new initiative is created.
        """
        # Should be notified
        manager_1 = create_new_user(email='manager_1@gmail.com',
                                    username='manager_1',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        # Should be notified too    
        manager_2 = create_new_user(email='manager_2@gmail.com',
                                    username='manager_2',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        # This user should not be in the reciepients
        volunteer = create_new_user(email='volunteer@gmail.com',
                                    username='volunteer',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)

        all_notifications = Notification.objects.all()
        notification = Notification.objects.filter(related_initiative__id=initiative.id).first()
        manager_1_notified = notification.recipients.contains(manager_1)
        manager_2_notified = notification.recipients.contains(manager_2)
        volunteer_not_notified = notification.recipients.contains(volunteer)
        creator_not_notified = notification.recipients.contains(self.initiative_creator)
        
        self.assertEqual(all_notifications.count(), 1)
        self.assertEqual(notification.recipients.count(), 2) # Only 2 users should be notified
        self.assertTrue(manager_1_notified)
        self.assertTrue(manager_2_notified)
        self.assertFalse(volunteer_not_notified)
        self.assertFalse(creator_not_notified)

    def test_notification_created_on_initiative_approval(self):
        """
        Tests that a notification is created when initaitive approved
        """
        
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)

        create_multiple_initiative_reviews(initiative=initiative,
                                            num_reviews=10,
                                            base_username='random',
                                            vote_type='approve',
                                            city=self.annaba_city,
                                            geo_location=self.point_in_annaba)
        # Run the evaluation task synchronously to get results immediatly
        evaluate_initiative_reviews_task(initiative_id=initiative.id)

        notification = Notification.objects.filter(notification_type='initiative_approved').first()
        
        creator_notified = notification.recipients.contains(self.initiative_creator)
        
        self.assertEqual(notification.recipients.count(), 1) # Only 1 users should be notified
        self.assertEqual(notification.related_initiative, initiative)
        self.assertTrue(creator_notified)

    def test_notification_created_on_initiative_review_failed_lack_of_reviews(self):
        """
        Tests that a notification is created when initaitive evaluation failed
        due to lack of reviews.
        """
        
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)

        create_multiple_initiative_reviews(initiative=initiative,
                                            num_reviews=1, # Less than minimum required reviews
                                            base_username='random',
                                            vote_type='approve',
                                            city=self.annaba_city,
                                            geo_location=self.point_in_annaba)
        
        # Run the evaluation task synchronously to get results immediatly
        evaluate_initiative_reviews_task(initiative_id=initiative.id)

        notification = Notification.objects.filter(notification_type='initiative_review_failed').first()
        
        creator_notified = notification.recipients.contains(self.initiative_creator)
        
        self.assertEqual(notification.recipients.count(), 1) # Only 1 users should be notified
        self.assertEqual(notification.related_initiative, initiative)
        self.assertEqual(notification.message, 'lack_of_reviews')
        self.assertTrue(creator_notified)
        
    def test_notification_created_on_initiative_review_failed_rejected_by_majority(self):
        """
        Tests that a notification is created when initaitive evaluation failed
        due to majority of reject reviews.
        """
        
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)

        create_multiple_initiative_reviews(initiative=initiative,
                                            num_reviews=10,
                                            base_username='random',
                                            vote_type='reject',
                                            city=self.annaba_city,
                                            geo_location=self.point_in_annaba)
        
        # Run the evaluation task synchronously to get results immediatly
        evaluate_initiative_reviews_task(initiative_id=initiative.id)

        notification = Notification.objects.filter(notification_type='initiative_review_failed').first()
        
        creator_notified = notification.recipients.contains(self.initiative_creator)
        
        self.assertEqual(notification.recipients.count(), 1) # Only 1 users should be notified
        self.assertEqual(notification.related_initiative, initiative)
        self.assertEqual(notification.message, 'rejected_by_managers')
        self.assertTrue(creator_notified)
        