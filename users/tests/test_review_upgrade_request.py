from django.conf import settings
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from users.models import City, UpgradeRequest
from users.tests.test_utils import create_new_user


@override_settings(SPATIAL_LAYER_PATHS=settings.TEST_SPATIAL_LAYER_PATHS)
class ReviewUpgradeRequestTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command('load_spatial_layers', 'DZ')
        cls.annaba_city = City.objects.get(name='Annaba')
        cls.point_in_annaba = cls.annaba_city.get_random_location_point()

    def setUp(self):
        self.client = Client()

    # -------------------------
    # Helpers
    # -------------------------
    def create_volunteer(self, username="volunteer"):
        return create_new_user(
            email=f"{username}@gmail.com",
            username=username,
            password="testpass123",
            phone_number="+213555447766",
            bio="Some bio",
            account_type="volunteer",
            city=self.annaba_city,
            geo_location=self.point_in_annaba,
        )

    def create_manager(self, username="manager"):
        return create_new_user(
            email=f"{username}@gmail.com",
            username=username,
            password="testpass123",
            phone_number="+213555447766",
            bio="Some bio",
            account_type="manager",
            city=self.annaba_city,
            geo_location=self.point_in_annaba,
        )

    def create_upgrade_request(self, user, status="pending"):
        return UpgradeRequest.objects.create(
            user=user, motivation="I am motivated", status=status
        )

    def login_as(self, user):
        self.client.login(username=user.username, password="testpass123")

    # -------------------------
    # Tests
    # -------------------------
    def test_volunteer_cannot_access_review_page(self):
        """Volunteers should not access or review upgrade requests."""
        volunteer = self.create_volunteer("volunteer1")
        volunteer_2 = self.create_volunteer("volunteer2")
        upgrade_request = self.create_upgrade_request(volunteer)

        self.login_as(volunteer_2)
        url = reverse("upgrade-request-review", args=[upgrade_request.id])

        get_response = self.client.get(url)
        post_response = self.client.post(url, {"vote": "approve", "note": "note"})

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(upgrade_request.reviews.count(), 0)

    def test_manager_cannot_review_non_pending_request(self):
        """Managers cannot review requests that are already approved/rejected."""
        volunteer = self.create_volunteer()
        manager = self.create_manager()
        self.login_as(manager)

        for status in ["approve", "rejected"]:
            upgrade_request = self.create_upgrade_request(volunteer, status=status)
            url = reverse("upgrade-request-review", args=[upgrade_request.id])

            get_response = self.client.get(url)
            post_response = self.client.post(url, {"vote": "reject", "note": "note"})

            self.assertEqual(get_response.status_code, 403)
            self.assertEqual(post_response.status_code, 403)
            self.assertEqual(upgrade_request.reviews.count(), 0)

    def test_manager_cannot_review_same_upgrade_request_more_than_once(self):
        """Managers cannot submit multiple reviews for the same request."""
        volunteer = self.create_volunteer()
        manager = self.create_manager()
        self.login_as(manager)

        upgrade_request = self.create_upgrade_request(volunteer)
        url = reverse("upgrade-request-review", args=[upgrade_request.id])

        # First review works
        first_post = self.client.post(url, {"vote": "reject", "note": "not qualified"})
        self.assertEqual(first_post.status_code, 302)  # redirect after success
        self.assertEqual(upgrade_request.reviews.count(), 1)
        
        review = upgrade_request.reviews.first()
        
        self.assertEqual(review.vote, "reject")
        self.assertEqual(review.manager, manager)

        # Second review is blocked
        second_post = self.client.post(url, {"vote": "approve", "note": "changed mind"})
        self.assertEqual(second_post.status_code, 403)
        self.assertEqual(upgrade_request.reviews.count(), 1)

    def test_manager_can_successfully_review_pending_request(self):
        """Managers can review a pending upgrade request."""
        volunteer = self.create_volunteer()
        manager = self.create_manager()
        self.login_as(manager)

        upgrade_request = self.create_upgrade_request(volunteer)
        url = reverse("upgrade-request-review", args=[upgrade_request.id])

        get_response = self.client.get(url)
        post_response = self.client.post(url, {"vote": "approve", "note": "Looks good"})

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(post_response.status_code, 302)
        self.assertEqual(upgrade_request.reviews.count(), 1)

        review = upgrade_request.reviews.first()
        self.assertEqual(review.manager, manager)
        self.assertEqual(review.vote, "approve")
        self.assertEqual(review.note, "Looks good")