from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from bson import ObjectId # For MongoDB ObjectId

from app.utils.enums import SubscriptionStatus
from app.schemas.plan_schemas import PlanResponse, PyObjectId # Import PlanResponse to nest plan details
                                                        # and PyObjectId for ID handling

class SubscriptionBase(BaseModel):
    # user_id will come from JWT, not typically in request body for create/update by user
    plan_id: PyObjectId = Field(..., description="The ID of the subscription plan to subscribe to")
    # For plan_id, if input is string, PyObjectId will validate and convert to ObjectId


class SubscriptionCreateRequest(BaseModel):
    """
    Schema for the request body when a user creates a new subscription.
    User only needs to provide the plan_id. user_id comes from JWT.
    """
    plan_id: PyObjectId = Field(..., description="The ID of the subscription plan")


class SubscriptionUpdateRequest(BaseModel):
    """
    Schema for the request body when a user updates (upgrades/downgrades) their subscription.
    User only needs to provide the new plan_id. user_id comes from JWT.
    """
    plan_id: PyObjectId = Field(..., description="The ID of the new subscription plan")


# Internal schema for service layer, including user_id
class SubscriptionCreateInternal(SubscriptionBase):
    user_id: str = Field(..., description="The ID of the user, derived from JWT")


class SubscriptionResponse(BaseModel):
    id: PyObjectId = Field(..., description="Unique identifier of the subscription")
    user_id: str = Field(..., description="The ID of the user")
    plan: PlanResponse = Field(..., description="Details of the subscribed plan") # Nested plan details
    start_date: datetime = Field(..., description="Subscription start date")
    end_date: datetime = Field(..., description="Subscription end date")
    status: SubscriptionStatus = Field(..., description="Current status of the subscription")
    created_at: datetime = Field(..., description="Timestamp of subscription creation")
    updated_at: datetime = Field(..., description="Timestamp of last subscription update")

    model_config = { # Pydantic V2
        "from_attributes": True,  # Allows creating schema from ORM/ODM model instances
        "json_encoders": {
            ObjectId: str, # Serialize MongoDB ObjectId to string
            datetime: lambda dt: dt.isoformat() # Standard ISO format for datetimes
            # Decimal is handled in PlanResponse's json_encoders
        },
        "use_enum_values": True # Serializes Enum members to their string values (e.g., "ACTIVE")
    }
    # For Pydantic V1:
    # class Config:
    #     orm_mode = True
    #     json_encoders = {
    #         ObjectId: str,
    #         datetime: lambda dt: dt.isoformat()
    #     }
    #     use_enum_values = True


class SubscriptionCancelResponse(BaseModel): # Optional: a simpler response for cancellation
    id: PyObjectId
    user_id: str
    status: SubscriptionStatus
    end_date: datetime # Show when it will truly expire
    message: str = "Subscription has been cancelled."

    model_config = { # Pydantic V2
        "from_attributes": True,
        "json_encoders": { ObjectId: str, datetime: lambda dt: dt.isoformat() },
        "use_enum_values": True
    }
    # Pydantic V1 equivalent for Config class