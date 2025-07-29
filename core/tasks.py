from celery import shared_task
from django.utils import timezone
from django.conf import settings
from core.models import Initiative

@shared_task
def evaluate_initiative_reviews_task(initiative_id):
    """
    Evaluates the overall outcome of an initiative's review period.

    This task is designed to be executed after the designated review period 
    for an initiative has ended (settings.settings.INITIATIVE_REVIEW_DURATION) 
    and it's scheduled in CreateInitiaiveView.

    Its primary purpose is to:
    1.  Retrieve the initiative specified by `initiative_id`.
    2.  Count the number of 'approve' and 'refuse' votes from the associated reviews.
    3.  Determine the final status of the initiative based on the voting results and configured thresholds:
        *   If the total number of reviews is less than the required minimum 
            (`settings.MIN_INITIATIVE_REVIEWS_REQUIRED`), the status is set to 'review_failed'.
        *   If the number of 'approve' votes is greater than or equal to'refuse' votes, and the minimum review count
            is met, the status is set to 'upcoming'. TODO: trigger next status transitions (ongoing, completed)
        *   In all other cases (e.g., more 'refuse' votes or exactly equal votes), the status is set to 
            'review_failed'.
    4.  Saves the updated initiative status to the database.

    This task ensures the review outcome is processed asynchronously, allowing the system to handle 
    potentially large numbers of initiatives and reviews without blocking user interactions or other 
    processes. It's typically scheduled to run automatically after settings.INITIATIVE_REVIEW_DURATION
    ends.
    """
    try:
        initiative = Initiative.objects.get(id=initiative_id)
        reviews = initiative.reviews.all()
        
        approve_count = reviews.filter(vote='approve').count()
        refuse_count = reviews.filter(vote='reject').count()
        total_reviews = approve_count + refuse_count

        # Not enough reviews -> review failed
        if total_reviews < settings.MIN_INITIATIVE_REVIEWS_REQUIRED:
            initiative.status = 'review_failed'
        # Approved by majority or reviews are equal -> change status to 'upcoming'
        # TODO: Schedule next status (ongoing then completed)
        elif approve_count >= refuse_count:
            initiative.status = 'upcoming'
            initiative.save()
        # More rejects than approves -> review failed
        else:
            initiative.status = 'review_failed'
 
        initiative.save()
        
    except Initiative.DoesNotExist:
        # Missing initiative do nothing
        pass
