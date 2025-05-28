from datetime import datetime, timezone
from flask import current_app  # 👈 Added for logging
from mongoengine.errors import DoesNotExist, NotUniqueError, ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed

from app.models.subscription import Subscription
from app.models.plan import Plan
from app.utils.enums import SubscriptionStatus
from app.schemas.subscription_schemas import SubscriptionCreateInternal, SubscriptionUpdateRequest


class SubscriptionService:

    @staticmethod
    def _get_active_subscription_for_user(user_id: str) -> Subscription | None:
        """Fetches the active subscription for a user, if any."""
        return Subscription.objects(user_id=user_id, status=SubscriptionStatus.ACTIVE).first()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def create_subscription(subscription_data: SubscriptionCreateInternal) -> Subscription:
        """Creates a new subscription for a user with validation and logging."""
        user_id = subscription_data.user_id
        plan_id = subscription_data.plan_id

        current_app.logger.info(f"Attempting to create subscription for user {user_id} with plan_id {plan_id} (type: {type(plan_id)})")

        existing_active_sub = SubscriptionService._get_active_subscription_for_user(user_id)
        if existing_active_sub:
            err_msg = "User already has an active subscription."
            current_app.logger.error(f"Create subscription error for user {user_id}: {err_msg}")
            raise ValueError(err_msg)

        try:
            plan = Plan.objects.get(id=plan_id)
            current_app.logger.info(f"Found plan: {plan.name} for plan_id {plan_id}")
        except (DoesNotExist, ValidationError) as e:
            err_msg = f"Plan with ID {plan_id} not found or invalid. MongoEngine error: {str(e)}"
            current_app.logger.error(f"Create subscription error for user {user_id}: {err_msg}")
            raise ValueError(err_msg)
        except Exception as e:
            err_msg = f"Unexpected error fetching plan {plan_id}: {str(e)}"
            current_app.logger.error(f"Create subscription error for user {user_id}: {err_msg}")
            raise ValueError(err_msg)

        new_sub = Subscription(
            user_id=user_id,
            plan=plan,
            start_date=datetime.now(timezone.utc),
            status=SubscriptionStatus.ACTIVE
        )
        new_sub._calculate_end_date()
        current_app.logger.info(f"New subscription object created (before save): user_id={new_sub.user_id}, plan_id={new_sub.plan.id}, end_date={new_sub.end_date}")

        try:
            new_sub.save()
            current_app.logger.info(f"Subscription saved successfully: id={new_sub.id}")
            return new_sub
        except (NotUniqueError, ValidationError) as e:
            err_msg = f"Database error (NotUnique/Validation) creating subscription: {str(e)}"
            current_app.logger.error(f"Create subscription error for user {user_id} during save: {err_msg}")
            raise ValueError(err_msg)
        except Exception as e:
            err_msg = f"Unexpected error creating subscription during save: {str(e)}"
            current_app.logger.error(f"Create subscription error for user {user_id} during save: {err_msg}")
            raise ValueError(err_msg)

    @staticmethod
    def get_subscription_details_for_user(user_id: str) -> Subscription | None:
        """Returns the active or most recent subscription after checking expiration."""
        SubscriptionService.check_and_expire_user_subscription(user_id)
        active_sub = SubscriptionService._get_active_subscription_for_user(user_id)
        return active_sub or Subscription.objects(user_id=user_id).order_by('-end_date').first()

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def update_user_subscription(user_id: str, update_data: SubscriptionUpdateRequest) -> Subscription:
        """Updates an active subscription to a new plan."""
        active_sub = SubscriptionService._get_active_subscription_for_user(user_id)
        if not active_sub:
            raise ValueError("No active subscription found to update.")

        new_plan_id = update_data.plan_id
        if active_sub.plan.id == new_plan_id:
            raise ValueError("User is already subscribed to this plan.")

        try:
            new_plan = Plan.objects.get(id=new_plan_id)
        except (DoesNotExist, ValidationError):
            raise ValueError(f"New plan with ID {new_plan_id} not found or invalid.")

        active_sub.plan = new_plan
        active_sub.start_date = datetime.now(timezone.utc)
        active_sub.status = SubscriptionStatus.ACTIVE
        active_sub._calculate_end_date()

        try:
            active_sub.save()
            return active_sub
        except (NotUniqueError, ValidationError) as e:
            raise ValueError(f"Database error updating subscription: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error updating subscription: {str(e)}")

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def cancel_user_subscription(user_id: str) -> Subscription:
        """Cancels a user's active subscription, allowing it to expire naturally."""
        active_sub = SubscriptionService._get_active_subscription_for_user(user_id)
        if not active_sub:
            raise ValueError("No active subscription found to cancel.")

        if active_sub.status == SubscriptionStatus.CANCELLED:
            raise ValueError("Subscription is already cancelled.")

        if active_sub.status == SubscriptionStatus.EXPIRED:
            raise ValueError("Cannot cancel an already expired subscription.")

        active_sub.status = SubscriptionStatus.CANCELLED

        try:
            active_sub.save()
            return active_sub
        except Exception as e:
            raise ValueError(f"Unexpected error cancelling subscription: {str(e)}")

    @staticmethod
    def check_and_expire_user_subscription(user_id: str) -> bool:
        """Expires a user's subscription if it has passed its end date."""
        subscription_to_expire = Subscription.objects(
            user_id=user_id,
            status=SubscriptionStatus.ACTIVE,
            end_date__lt=datetime.now(timezone.utc)
        ).first()

        if subscription_to_expire:
            subscription_to_expire.status = SubscriptionStatus.EXPIRED
            try:
                subscription_to_expire.save()
                current_app.logger.info(f"Subscription {subscription_to_expire.id} for user {user_id} expired.")
                return True
            except Exception as e:
                current_app.logger.error(f"Error saving expired status for sub {subscription_to_expire.id}: {e}")
        return False

    @staticmethod
    def expire_all_due_subscriptions():
        """Scheduled task: Marks all overdue subscriptions as EXPIRED."""
        subscriptions_to_expire = Subscription.objects(
            status=SubscriptionStatus.ACTIVE,
            end_date__lt=datetime.now(timezone.utc)
        )
        expired_count = 0
        for sub in subscriptions_to_expire:
            sub.status = SubscriptionStatus.EXPIRED
            try:
                sub.save()
                expired_count += 1
            except Exception as e:
                current_app.logger.error(f"Error expiring subscription {sub.id}: {e}")

        if expired_count > 0:
            current_app.logger.info(f"Expired {expired_count} subscriptions.")
