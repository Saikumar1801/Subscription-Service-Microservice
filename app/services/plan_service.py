from app.models.plan import Plan
from app.schemas.plan_schemas import PlanCreate, PlanUpdate # Not used yet but defined
from mongoengine.errors import NotUniqueError, ValidationError, DoesNotExist

class PlanService:
    @staticmethod
    def get_all_plans() -> list[Plan]:
        try:
            return list(Plan.objects.all().order_by('name'))
        except Exception as e:
            print(f"Error fetching all plans: {e}")
            return []

    @staticmethod
    def get_plan_by_id(plan_id: str) -> Plan | None:
        try:
            return Plan.objects.get(id=plan_id)
        except (DoesNotExist, ValidationError):
            return None
        except Exception as e:
            print(f"Error fetching plan by ID {plan_id}: {e}")
            return None
    
    # ... (create_plan, update_plan, delete_plan methods from before, if you included them)