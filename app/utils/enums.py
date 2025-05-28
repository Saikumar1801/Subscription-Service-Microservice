import enum

class SubscriptionStatus(str, enum.Enum): # Inheriting from str makes it directly JSON serializable
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE" # Could be used if payment fails, or before first payment
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

    @classmethod
    def _missing_(cls, value): # Handles case-insensitive matching if needed
        if isinstance(value, str):
            for member in cls:
                if member.value == value.upper():
                    return member
        return None # Or raise error