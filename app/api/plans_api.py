from flask import Blueprint, jsonify, current_app
from app.services.plan_service import PlanService
from app.schemas.plan_schemas import PlanResponse

plans_bp = Blueprint('plans_bp', __name__)
plan_service = PlanService()

@plans_bp.route('/plans', methods=['GET'])
def get_all_plans_endpoint():
    try:
        plans_from_db = plan_service.get_all_plans()
        response_data = []
        for plan_model in plans_from_db:
            try:
                plan_schema_instance = PlanResponse.model_validate(plan_model) # Pydantic V2
                # plan_schema_instance = PlanResponse.from_orm(plan_model) # Pydantic V1
                response_data.append(plan_schema_instance.model_dump(mode='json')) # Pydantic V2
                # response_data.append(plan_schema_instance.dict()) # Pydantic V1
            except Exception as e:
                current_app.logger.error(f"Error serializing plan {getattr(plan_model, 'id', 'UNKNOWN_ID')}: {e}")
                continue
        return jsonify(response_data), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_all_plans_endpoint: {e}")
        return jsonify({"error": "An unexpected error occurred while retrieving plans."}), 500

@plans_bp.route('/plans/<string:plan_id>', methods=['GET'])
def get_plan_by_id_endpoint(plan_id: str):
    try:
        plan_model = plan_service.get_plan_by_id(plan_id)
        if not plan_model:
            return jsonify({"error": "Plan not found"}), 404
        plan_schema_instance = PlanResponse.model_validate(plan_model) # Pydantic V2
        # plan_schema_instance = PlanResponse.from_orm(plan_model) # Pydantic V1
        return jsonify(plan_schema_instance.model_dump(mode='json')), 200 # Pydantic V2
        # return jsonify(plan_schema_instance.dict()), 200 # Pydantic V1
    except Exception as e:
        current_app.logger.error(f"Error in get_plan_by_id_endpoint for ID {plan_id}: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500