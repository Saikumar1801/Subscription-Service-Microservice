from flask import Blueprint, request, jsonify, current_app, g
from pydantic import ValidationError

from app.services.subscription_service import SubscriptionService
from app.schemas.subscription_schemas import (
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
    SubscriptionResponse,
    SubscriptionCreateInternal
)
from app.core.security import jwt_required, get_current_user_id

# This is the correct way: Define the blueprint in this file.
# This line should have been present from our initial setup of this file.
subscriptions_bp = Blueprint('subscriptions_bp', __name__)

# DO NOT use: from . import subscriptions_bp (this was the error)

subscription_service = SubscriptionService()

@subscriptions_bp.route('/subscriptions', methods=['POST'])
@jwt_required
def create_subscription_endpoint():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "User ID not found in token"}), 401
    try:
        request_data = SubscriptionCreateRequest(**request.json)
    except ValidationError as e:
        return jsonify({"error": "Invalid request data", "details": e.errors()}), 400
    except Exception:
        return jsonify({"error": "Invalid request body or content type"}), 400

    internal_sub_data = SubscriptionCreateInternal(
        user_id=user_id,
        plan_id=request_data.plan_id
    )
    try:
        new_subscription = subscription_service.create_subscription(internal_sub_data)
        response_data = SubscriptionResponse.model_validate(new_subscription).model_dump(mode='json')
        return jsonify(response_data), 201
    except ValueError as e:
        status_code = 409 # Default to conflict
        if "not found" in str(e).lower():
            status_code = 404
        return jsonify({"error": str(e)}), status_code
    except Exception as e:
        current_app.logger.error(f"Error creating subscription for user {user_id}: {e}")
        return jsonify({"error": "Could not create subscription."}), 500

@subscriptions_bp.route('/subscriptions/<string:user_id_param>', methods=['GET'])
@jwt_required
def get_user_subscription_endpoint(user_id_param: str):
    token_user_id = get_current_user_id()
    if token_user_id != user_id_param:
        return jsonify({"error": "Forbidden: You can only access your own subscription details."}), 403
    try:
        subscription = subscription_service.get_subscription_details_for_user(token_user_id)
        if not subscription:
            return jsonify({"message": "No subscription found for this user."}), 404
        response_data = SubscriptionResponse.model_validate(subscription).model_dump(mode='json')
        return jsonify(response_data), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving subscription for user {token_user_id}: {e}")
        return jsonify({"error": "Could not retrieve subscription details."}), 500

@subscriptions_bp.route('/subscriptions/<string:user_id_param>', methods=['PUT'])
@jwt_required
def update_user_subscription_endpoint(user_id_param: str):
    token_user_id = get_current_user_id()
    if token_user_id != user_id_param:
        return jsonify({"error": "Forbidden: You can only update your own subscription."}), 403
    try:
        request_data = SubscriptionUpdateRequest(**request.json)
    except ValidationError as e:
        return jsonify({"error": "Invalid request data", "details": e.errors()}), 400
    except Exception:
        return jsonify({"error": "Invalid request body or content type"}), 400
    try:
        updated_subscription = subscription_service.update_user_subscription(token_user_id, request_data)
        response_data = SubscriptionResponse.model_validate(updated_subscription).model_dump(mode='json')
        return jsonify(response_data), 200
    except ValueError as e:
        status_code = 409
        if "not found" in str(e).lower():
            status_code = 404
        return jsonify({"error": str(e)}), status_code
    except Exception as e:
        current_app.logger.error(f"Error updating subscription for user {token_user_id}: {e}")
        return jsonify({"error": "Could not update subscription."}), 500

@subscriptions_bp.route('/subscriptions/<string:user_id_param>', methods=['DELETE'])
@jwt_required
def cancel_user_subscription_endpoint(user_id_param: str):
    token_user_id = get_current_user_id()
    if token_user_id != user_id_param:
        return jsonify({"error": "Forbidden: You can only cancel your own subscription."}), 403
    try:
        cancelled_subscription = subscription_service.cancel_user_subscription(token_user_id)
        response_data = SubscriptionResponse.model_validate(cancelled_subscription).model_dump(mode='json')
        return jsonify(response_data), 200
    except ValueError as e:
        status_code = 409
        if "not found" in str(e).lower():
            status_code = 404
        return jsonify({"error": str(e)}), status_code
    except Exception as e:
        current_app.logger.error(f"Error cancelling subscription for user {token_user_id}: {e}")
        return jsonify({"error": "Could not cancel subscription."}), 500