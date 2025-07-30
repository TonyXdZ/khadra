from django.utils import timezone
from django.core.management import call_command
from django.test import Client, TestCase
from users.models import City
from users.tests.test_utils import create_new_user
from core.models import Initiative
from core.tests.test_utils import create_initiative, create_multiple_initiative_reviews
from core.tasks import (evaluate_initiative_reviews_task, 
                        transition_initiative_to_ongoing_task, 
                        transition_initiative_to_completed_task)



class CeleryTasksTestCase(TestCase):

    @classmethod
    def setUpTestData(self):
        call_command('load_spatial_layers', 'DZ')
        self.client_1 = Client()
        self.client_2 = Client()
        self.annaba_city = City.objects.get(name='Annaba')
        self.point_in_annaba = self.annaba_city.get_random_location_point()
        self.initiative_creator = create_new_user(email='initiative_starter_user@gmail.com',
                                username='initiative_starter_user',
                                password='qsdflkjlkj',
                                account_type='manager',
                                phone_number='+213555447755', 
                                bio='Some good bio',
                                city=self.annaba_city,
                                geo_location=self.point_in_annaba,
                                )

    def test_initiative_evaluation_when_reviews_not_enough(self):
        """
        Tests that an initiative status is marked as 'review_failed' if it does not receive
        the minimum required number of reviews by the end of the review period.
        """
                                
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        
        # Min reviews required is in settings.MIN_INITIATIVE_REVIEWS_REQUIRED
        reviews = create_multiple_initiative_reviews(initiative=initiative, 
                                                num_reviews=2, 
                                                base_username='',
                                                vote_type='approve',
                                                city=self.annaba_city,
                                                geo_location=self.point_in_annaba)
        
        # Run the task synchronously to get immediat results
        evaluate_initiative_reviews_task(initiative_id=initiative.id)
        
        # Refresh the instance
        initiative.refresh_from_db()
        self.assertEqual( initiative.status, 'review_failed')

    def test_initiative_evaluation_when_most_reviewers_reject(self):
        """
        Tests that an initiative status is marked as 'review_failed' if majority
        of reviews are 'reject'.
        """
                                
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        
        # Min reviews required is in settings.MIN_INITIATIVE_REVIEWS_REQUIRED
        reviews = create_multiple_initiative_reviews(initiative=initiative, 
                                                num_reviews=10, 
                                                base_username='',
                                                vote_type='reject',
                                                city=self.annaba_city,
                                                geo_location=self.point_in_annaba)
        
        # Run the task synchronously to get immediat results
        evaluate_initiative_reviews_task(initiative_id=initiative.id)
        
        # Refresh the instance
        initiative.refresh_from_db()
        self.assertEqual( initiative.status, 'review_failed')

    def test_initiative_evaluation_when_reject_and_approve_reviews_are_equal(self):
        """
        Tests that an initiative status is marked as 'upcoming' if approve
        and reject reviews are equal.
        Why?
        because we wanna make Algeria green.
        """
                                
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        
        # Min reviews required is in settings.MIN_INITIATIVE_REVIEWS_REQUIRED
        reject_reviews = create_multiple_initiative_reviews(initiative=initiative, 
                                                num_reviews=5,
                                                base_username='lazy',
                                                vote_type='reject',
                                                city=self.annaba_city,
                                                geo_location=self.point_in_annaba)
        
        approve_reviews = create_multiple_initiative_reviews(initiative=initiative, 
                                                num_reviews=5,
                                                base_username='active',
                                                vote_type='approve',
                                                city=self.annaba_city,
                                                geo_location=self.point_in_annaba)
        
        # Run the task synchronously to get immediat results
        evaluate_initiative_reviews_task(initiative_id=initiative.id)
        
        # Refresh the instance
        initiative.refresh_from_db()
        self.assertEqual( initiative.status, 'upcoming')

    def test_initiative_evaluation_when_most_reviewers_approve(self):
        """
        Tests that an initiative status is marked as 'upcoming'
        if majority of reviews are approve.
        """
                                
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        
        # Min reviews required is in settings.MIN_INITIATIVE_REVIEWS_REQUIRED
        reject_reviews = create_multiple_initiative_reviews(initiative=initiative, 
                                                num_reviews=4,
                                                base_username='lazy',
                                                vote_type='reject',
                                                city=self.annaba_city,
                                                geo_location=self.point_in_annaba)
        
        approve_reviews = create_multiple_initiative_reviews(initiative=initiative, 
                                                num_reviews=6,
                                                base_username='active',
                                                vote_type='approve',
                                                city=self.annaba_city,
                                                geo_location=self.point_in_annaba)
        
        # Run the task synchronously to get immediat results
        evaluate_initiative_reviews_task(initiative_id=initiative.id)
        
        # Refresh the instance
        initiative.refresh_from_db()
        self.assertEqual( initiative.status, 'upcoming')
    
    def test_status_transition_schedule_to_ongoing_after_evaluation(self):
        """
        Tests that an initiative status is marked as 'ongoing'
        at initiative scheduled datetime.
        """
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba,
                                        scheduled_datetime=timezone.now())
        initiative.status = 'upcoming'
        initiative.save()
        transition_initiative_to_ongoing_task(initiative_id=initiative.id)
        
        # Refresh the instance
        initiative.refresh_from_db()
        self.assertEqual( initiative.status, 'ongoing')

    def test_status_transition_schedule_to_completed(self):
        """
        Tests that an initiative status is marked as 'completed' 
        at initiative end time.
        """
        # Default initiative duration is 1 day we set the scheduled datetime
        # to yesterday to mimic real life initiatives
        yesterday = timezone.now() - timezone.timedelta(days=1)
        
        initiative = create_initiative(created_by=self.initiative_creator,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba,
                                        scheduled_datetime=yesterday)
        initiative.status = 'ongoing'
        initiative.save()
        transition_initiative_to_completed_task(initiative_id=initiative.id)
        
        # Refresh the instance
        initiative.refresh_from_db()
        self.assertEqual( initiative.status, 'completed')

    
        
