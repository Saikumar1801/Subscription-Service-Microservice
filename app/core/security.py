from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from datetime import datetime, timedelta, timezone

# This is a simplified JWT setup. For production, consider robust libraries.

def generate_token(user_id: any, expires_delta_minutes: int = 60 * 24 * 7) -> str: # e.g., 7 days
    """
    Generates a JWT token.
    For testing purposes, you might call this from a temporary endpoint or script.
    """
    secret_key = current_app.config['SECRET_KEY']
    algorithm = current_app.config['JWT_ALGORITHM']
    
    if not secret_key or not algorithm:
        raise ValueError("SECRET_KEY and JWT_ALGORITHM must be configured in the Flask app.")

    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)
    to_encode = {
        "exp": expire,
        "iat": datetime.now(timezone.utc), # Issued at
        "sub": str(user_id)  # Subject (user_id)
    }
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt

def decode_token(token: str) -> dict | None:
    """
    Decodes a JWT token.
    Returns the payload if valid, None otherwise.
    """
    secret_key = current_app.config['SECRET_KEY']
    algorithms = [current_app.config['JWT_ALGORITHM']] # PyJWT expects a list of algorithms

    if not secret_key or not algorithms[0]:
        current_app.logger.error("JWT SECRET_KEY or JWT_ALGORITHM not configured for decoding.")
        return None # Or raise an error

    try:
        payload = jwt.decode(token, secret_key, algorithms=algorithms)
        return payload
    except jwt.ExpiredSignatureError:
        current_app.logger.warning("Token has expired.")
        return None 
    except jwt.InvalidTokenError as e:
        current_app.logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e: # Catch any other unexpected JWT errors
        current_app.logger.error(f"Error decoding token: {e}")
        return None

def jwt_required(f):
    """
    Decorator to protect routes that require JWT authentication.
    Extracts user_id from token and stores it in Flask's 'g.user_id'.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token = None

        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401

        parts = auth_header.split()

        if parts[0].lower() != 'bearer':
            return jsonify({"error": "Invalid Authorization header format. Expected 'Bearer <token>'"}), 401
        elif len(parts) == 1:
            return jsonify({"error": "Token not found after 'Bearer'"}), 401
        elif len(parts) > 2:
            return jsonify({"error": "Invalid Authorization header format. Too many parts."}), 401
        
        token = parts[1]

        if not token: # Should be caught by len(parts) == 1, but defensive
            return jsonify({"error": "Token is missing"}), 401

        payload = decode_token(token)

        if payload is None:
            # decode_token logs specific errors (expired, invalid)
            return jsonify({"error": "Invalid or expired token"}), 401

        user_id_from_token = payload.get('sub')
        if not user_id_from_token:
            return jsonify({"error": "Token does not contain user identifier ('sub' claim)"}), 401
        
        g.user_id = user_id_from_token # Store user_id in Flask's global context 'g'
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id() -> str | None:
    """
    Helper function to retrieve the current user's ID from Flask's 'g' object.
    Returns None if no user_id is set (e.g., route is not @jwt_required or token was invalid).
    """
    return getattr(g, 'user_id', None)

# Optional: Admin-specific decorator (if you had roles)
# def admin_required(f):
#     @wraps(f)
#     @jwt_required # Ensures user is authenticated first
#     def decorated_function(*args, **kwargs):
#         user_id = get_current_user_id()
#         # Example: Check if user_id belongs to an admin
#         # This would typically involve a database lookup or checking another claim in the token
#         if not is_admin(user_id): # is_admin() is a hypothetical function
#             return jsonify({"error": "Administrator access required"}), 403
#         return f(*args, **kwargs)
#     return decorated_function