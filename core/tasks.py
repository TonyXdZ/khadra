from celery import shared_task
from django.utils import timezone
from django.conf import settings
from core.models import Initiative
from notifications.signals import ( initiative_approved_signal,
                                    initiative_review_failed_signal)


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
            is met, the status is set to 'upcoming'.
        *   In all other cases (e.g., more 'refuse' votes or exactly equal votes), the status is set to 
            'review_failed'.
    4.  Saves the updated initiative status to the database.
    5. Emit proper custom signal from notifications.signals

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
            # Emit initiative review failed signal with 'lack_of_reviews' reason
            initiative_review_failed_signal.send(sender=Initiative, 
                                                instance=initiative, 
                                                reason='lack_of_reviews')
        
        # Approved by majority or reviews are equal -> change status to 'upcoming'
        elif approve_count >= refuse_count:
            initiative.status = 'upcoming'
            initiative.save()
            # Emit initiative approved signal for notifications
            initiative_approved_signal.send(sender=Initiative, instance=initiative,)
            # Schedule transition to 'ongoing' at the initiative's scheduled start time
            if initiative.scheduled_datetime > timezone.now():
                transition_initiative_to_ongoing_task.apply_async(
                    args=[initiative.id],
                    eta=initiative.scheduled_datetime
                )

            # Schedule transition to 'completed' at the initiative's calculated end time
            # Ensure get_end_datetime() returns a timezone-aware datetime
            end_datetime = initiative.get_end_datetime()
            if end_datetime and end_datetime > timezone.now():
                transition_initiative_to_completed_task.apply_async(
                    args=[initiative.id],
                    eta=end_datetime
                )
            
        # More rejects than approves -> review failed
        else:
            initiative.status = 'review_failed'
            # Emit initiative review failed signal with 'rejected_by_managers' reason
            initiative_review_failed_signal.send(sender=Initiative, 
                                                instance=initiative, 
                                                reason='rejected_by_managers')
 
        initiative.save()
        
    except Initiative.DoesNotExist:
        # Missing initiative do nothing
        pass


@shared_task
def transition_initiative_to_ongoing_task(initiative_id):
    """
    Transitions an initiative's status to 'ongoing'.

    This task is intended to be scheduled to run at the initiative's
    `scheduled_datetime`. It checks if the initiative is still in the
    'upcoming' status and eligible for transition.

    Args:
        initiative_id (int): The ID of the Initiative to transition.
    """
    try:
        initiative = Initiative.objects.get(id=initiative_id)

        # Only transition if it's still 'upcoming'
        if initiative.status == 'upcoming':
            initiative.status = 'ongoing'
            initiative.save()
    
    except Initiative.DoesNotExist:
        # Missing initiative do nothing
        pass


@shared_task
def transition_initiative_to_completed_task(initiative_id):
    """
    Transitions an initiative's status to 'completed'.

    This task is intended to be scheduled to run at the initiative's
    end time (obtained via `initiative.get_end_datetime()`). It checks
    if the initiative is in 'ongoing' or 'upcoming' status and eligible
    for completion.

    Args:
        initiative_id (int): The ID of the Initiative to transition.
    """
    try:
        initiative = Initiative.objects.get(id=initiative_id)

        # Transition if it's 'ongoing' or still 'upcoming' (maybe it started late)
        if initiative.status in ['ongoing', 'upcoming']:
            initiative.status = 'completed'
            initiative.save()

    except Initiative.DoesNotExist:
        # Missing initiative do nothing
        pass