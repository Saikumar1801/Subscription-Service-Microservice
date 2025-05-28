from mongoengine import (
    Document,
    StringField,
    ReferenceField, # To link to the Plan document
    DateTimeField,
    EnumField,      # To store the subscription status
    # QuerySet
)
from datetime import datetime, timedelta
from app.models.plan import Plan # Import the Plan model
from app.utils.enums import SubscriptionStatus # Import our status enum

# Optional: Base document for timestamps, similar to Plan model
# from .base import BaseDocument # If you created a BaseDocument with save override

class Subscription(Document): # Or Subscription(BaseDocument):
    """
    Represents a user's subscription to a plan.
    """
    meta = {
        'collection': 'subscriptions',
        'indexes': [
            'user_id',
            'status',
            ('user_id', 'status'), # Compound index for finding user's active/inactive subs
            'end_date' # For the expiration checker task
        ]
    }

    user_id = StringField(required=True) # Assuming user ID is a string from JWT 'sub'
    plan = ReferenceField(Plan, required=True) # Reference to a Plan document
    
    start_date = DateTimeField(required=True, default=datetime.utcnow)
    end_date = DateTimeField(required=True) # Will be calculated based on plan duration
    
    status = EnumField(SubscriptionStatus, required=True, default=SubscriptionStatus.ACTIVE)

    # Timestamps
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        """Override save to update timestamps and ensure end_date calculation if needed."""
        if not self.created_at:
            self.created_at = datetime.utcnow()
        
        # If end_date is not set and plan is available, calculate it.
        # This is more of a creation-time logic; updates might handle end_date differently.
        if not self.end_date and self.plan and hasattr(self.plan, 'duration_days'):
             self._calculate_end_date()

        self.updated_at = datetime.utcnow()
        return super(Subscription, self).save(*args, **kwargs)

    def _calculate_end_date(self):
        """Helper to calculate end_date based on start_date and plan duration."""
        if self.start_date and self.plan and self.plan.duration_days:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        else:
            # Fallback or raise error if essential info is missing
            # This should ideally not happen if data is validated before saving
            pass 

    def __repr__(self):
        plan_name = self.plan.name if self.plan else "N/A"
        return f'<Subscription id={self.id} user_id="{self.user_id}" plan="{plan_name}" status="{self.status.value}">'