from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v, _): # Removed validation_info for broader Pydantic compatibility
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema): # Pydantic V2
         field_schema.update(type="string")
    # For Pydantic V1, uncomment below if needed, or use json_encoders in Config
    # @classmethod
    # def __modify_schema__(cls, field_schema):
    #     field_schema.update(type="string")

class PlanBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Name of the subscription plan")
    price: Decimal = Field(..., gt=0, description="Price of the plan")
    features: Optional[List[str]] = Field(default_factory=list, description="List of features included in the plan")
    duration_days: int = Field(..., gt=0, description="Duration of the plan in days")
    
    model_config = { # Pydantic V2
        "json_encoders": { Decimal: float }
    }
    # class Config: # Pydantic V1
    #     json_encoders = { Decimal: float }

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0)
    features: Optional[List[str]] = None
    duration_days: Optional[int] = Field(None, gt=0)

class PlanResponse(PlanBase):
    id: PyObjectId = Field(..., description="Unique identifier of the plan")
    created_at: datetime = Field(..., description="Timestamp of plan creation")
    updated_at: datetime = Field(..., description="Timestamp of last plan update")

    model_config = { # Pydantic V2
        "from_attributes": True,
        "json_encoders": {
            ObjectId: str,
            Decimal: float,
            datetime: lambda dt: dt.isoformat()
        }
    }
    # class Config: # Pydantic V1
    #     orm_mode = True
    #     json_encoders = {
    #         ObjectId: str,
    #         Decimal: float,
    #         datetime: lambda dt: dt.isoformat()
    #     }