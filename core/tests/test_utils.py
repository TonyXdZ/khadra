from django.utils import timezone
from core.models import Initiative, InitiativeReview
from users.tests.test_utils import create_new_user

DATE_IN_THE_FUTUR = timezone.now() + timezone.timedelta(days=15)

def create_initiative(created_by, info, city, geo_location, required_volunteers=10, scheduled_datetime=DATE_IN_THE_FUTUR):
    """
    Creates Initiative instance for testing purposes

    Args:
        created_by (User): The user creating the initiative.
        info (str): Information about the initiative.
        city (City): City instance where the initiative is located.
        geo_location (Point): Geo location point (e.g., Point(x, y)).
        scheduled_datetime (datetime): The planned date and time for the initiative. Default 15 days.
        required_volunteers (int, optional): Number of volunteers needed. Defaults to 10.

    Returns:
        Initiative: The created Initiative object.

    Example Usage:
        Assuming you have a 'creator_user', 'test_city' (City instance), 
        and 'initiative_location' (Point object) available

        from django.utils import timezone
        from datetime import timedelta
        
        creator_user = User.objects.get(username='initiative_creator')
        test_city = City.objects.get(name='Djelfa')
        initiative_location = Point(5.0, 10.0)
        
        future_datetime = timezone.now() + timedelta(days=10)
        
        initiative = create_initiative(
            created_by=creator_user,
            info="a lot of info.",
            city=test_city,
            geo_location=initiative_location,
            scheduled_datetime=future_datetime,
            required_volunteers=20
        )
    """
    initiative = Initiative.objects.create(
        created_by=created_by,
        info=info,
        city=city,
        geo_location=geo_location,
        scheduled_datetime=scheduled_datetime,
        required_volunteers=required_volunteers,
    )
    return initiative


def create_multiple_initiative_reviews(initiative, num_reviews, base_username, vote_type, city, geo_location):
    """
    Creates multiple initiative reviews for testing purposes with the same vote.

    This helper function simplifies setting up test data by creating a specified
    number of reviewer users and associated InitiativeReview instances. All
    created reviews will have the same specified vote (e.g., 'approve' or 'reject').
    Reviewer details are generated programmatically. Reviews are created and saved
    individually.

    Args:
        initiative (Initiative): The Initiative object the reviews are for.
        num_reviews (int): The number of reviews to create.
        base_username (str): Unique string to use each time the function executes to avoid same usernames and emails.
        vote_type (str): The vote value for all created reviews (e.g., 'approve', 'reject').
        city (City): City instance.
        geo_location (Point): geolocation point.

    Returns:
        list: A list of the created InitiativeReview objects.
        
    Example Usage:
        # Assuming you have an 'initiative' object
        # Create 5 reviews, all voting 'approve'
        approve_reviews = create_multiple_initiative_reviews(initiative, 5, 'approve')
        
        # Create 3 reviews, all voting 'reject'
        reject_reviews = create_multiple_initiative_reviews(initiative, 3, 'reject')
    """
    created_reviews = []
    base_email = base_username + "{}@test.com"
    base_username = base_username + "{}"
    base_phone = "+2135550000{:02d}"

    for i in range(num_reviews):
        # Create reviewer user
        reviewer = create_new_user(
            email=base_email.format(i),
            username=base_username.format(i),
            password='qsdflkjlkj',
            account_type='manager',
            phone_number=base_phone.format(i),
            bio=f'Bio for reviewer {i}',
            city=city,
            geo_location=geo_location,
        )

        # Create and save the InitiativeReview instance with the specified vote
        review = InitiativeReview.objects.create(
            initiative=initiative,
            vote=vote_type,
            manager=reviewer,
        )
        created_reviews.append(review)

    return created_reviews