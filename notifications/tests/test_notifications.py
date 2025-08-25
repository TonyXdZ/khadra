from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from users.models import Profile, City, UpgradeRequest
from users.tests.test_utils import create_new_user
from core.tests.test_utils import create_initiative, create_multiple_initiative_reviews
from notifications.models import Notification
from core.tasks import (evaluate_initiative_reviews_task, 
                        transition_initiative_to_ongoing_task, 
                        transition_initiative_to_completed_task)

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
        
    def test_notification_created_on_initiative_started(self):
        """
        Tests that a notification is created when initaitive starts.
        """
        
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba,
                                        scheduled_datetime=timezone.now())
        
        volunteer = create_new_user(email='volunteer@gmail.com',
                                    username='volunteer',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        volunteer_2 = create_new_user(email='volunteer_2@gmail.com',
                                    username='volunteer_2',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        # Add volunteers to the instance to verify if they get notified
        initiative.volunteers.add(volunteer, volunteer_2)
        initiative.status = 'upcoming'
        initiative.save()
        transition_initiative_to_ongoing_task(initiative_id=initiative.id)
        
        notification = Notification.objects.filter(notification_type='initiative_started').first()
        
        creator_notified = notification.recipients.contains(self.initiative_creator)
        volunteer_notified = notification.recipients.contains(volunteer)
        volunteer_2_notified = notification.recipients.contains(volunteer_2)
        # 3 users should be notified
        # initiative creator, volunteer, volunteer_2
        self.assertEqual(notification.recipients.count(), 3)
        self.assertEqual(notification.related_initiative, initiative)
        self.assertTrue(volunteer_notified)
        self.assertTrue(volunteer_2_notified)
        
    def test_notification_created_on_initiative_completed(self):
        """
        Tests that a notification is created when initaitive completed.
        """
        # Since the default initiative duration is 1 day, setting scheduled_datetime to
        # yesterday makes the initiative end today — simulating a realistic past case.
        yesterday = timezone.now() - timezone.timedelta(days=1)
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba,
                                        scheduled_datetime=yesterday)
        
        volunteer = create_new_user(email='volunteer@gmail.com',
                                    username='volunteer',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        volunteer_2 = create_new_user(email='volunteer_2@gmail.com',
                                    username='volunteer_2',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        # Add volunteers to the instance to verify if they get notified
        initiative.volunteers.add(volunteer, volunteer_2)
        initiative.status = 'ongoing'
        initiative.save()
        transition_initiative_to_completed_task(initiative_id=initiative.id)
        
        notification = Notification.objects.filter(notification_type='initiative_completed').first()
        
        creator_notified = notification.recipients.contains(self.initiative_creator)
        volunteer_notified = notification.recipients.contains(volunteer)
        volunteer_2_notified = notification.recipients.contains(volunteer_2)
        # 3 users should be notified
        # initiative creator, volunteer, volunteer_2
        self.assertEqual(notification.recipients.count(), 3)
        self.assertEqual(notification.related_initiative, initiative)
        self.assertTrue(creator_notified)
        self.assertTrue(volunteer_notified)
        self.assertTrue(volunteer_2_notified)

    def test_notification_listview(self):
        """
        Verify notifications ListView shows only current user related notifications.
        """
        user = create_new_user(email='user@gmail.com',
                                    username='user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        # This will generate an initiative_created notification for all managers
        # thats why we started with notification_2 because this will be the first notification
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba,
                                        scheduled_datetime=timezone.now())

        
        notification_2 = Notification.objects.create(notification_type='initiative_approved', related_initiative=initiative)
        notification_3 = Notification.objects.create(notification_type='initiative_review_failed', related_initiative=initiative)
        notification_4 = Notification.objects.create(notification_type='initiative_started', related_initiative=initiative)
        notification_5 = Notification.objects.create(notification_type='initiative_cancelled', related_initiative=initiative)
        notification_6 = Notification.objects.create(notification_type='initiative_completed', related_initiative=initiative)
        # Announcement should be is_broadcast and it should be included
        # in the user notifications even when he is not added in reciepients
        notification_7 = Notification.objects.create(notification_type='announcement', is_broadcast=True)
        
        notification_2.recipients.add(user)
        notification_3.recipients.add(user)
        notification_4.recipients.add(user)
        notification_5.recipients.add(user)
        notification_6.recipients.add(user)
        
        # User is not added as a reciepient and there is no broadcast notification here
        excluded_notification_2 = Notification.objects.create(notification_type='initiative_approved', related_initiative=initiative)
        excluded_notification_3 = Notification.objects.create(notification_type='initiative_review_failed', related_initiative=initiative)
        excluded_notification_4 = Notification.objects.create(notification_type='initiative_started', related_initiative=initiative)
        excluded_notification_5 = Notification.objects.create(notification_type='initiative_cancelled', related_initiative=initiative)
        excluded_notification_6 = Notification.objects.create(notification_type='initiative_completed', related_initiative=initiative)
        # Excluded announcement because it was created before user joined
        yesterday = timezone.now() - timezone.timedelta(days=1)
        excluded_notification_7 = Notification.objects.create(notification_type='announcement', 
                                                            is_broadcast=True,
                                                            created_at=yesterday)

        client = Client()
        client.login(username='user', password='qsdflkjlkj')
        
        response = client.get(reverse('notifications-list'))
        notifications = response.context['notifications']
        
        self.assertEqual( notifications.count(), 7)

    def test_notification_created_on_upgrade_request_created(self):
        """
        Tests that a notification is created and sent to all managers 
        when a new upgrade request is created.
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

        # User requesting upgrade
        volunteer = create_new_user(email='volunteer@gmail.com',
                                    username='volunteer',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        upgrade_request = UpgradeRequest.objects.create(user=volunteer, motivation="Im a nice person...")

        all_notifications = Notification.objects.all()
        notification = Notification.objects.filter(related_upgrade_request__id=upgrade_request.id).first()
        manager_notified = notification.recipients.contains(self.initiative_creator)
        manager_1_notified = notification.recipients.contains(manager_1)
        manager_2_notified = notification.recipients.contains(manager_2)
        volunteer_not_notified = notification.recipients.contains(volunteer)

        self.assertEqual(all_notifications.count(), 1)
        # Only 3 users should be notified manager_user (self.initiative_creator)
        # manager_1 and manager_2
        self.assertEqual(notification.recipients.count(), 3)
        self.assertTrue(manager_notified)
        self.assertTrue(manager_1_notified)
        self.assertTrue(manager_2_notified)
        self.assertFalse(volunteer_not_notified)