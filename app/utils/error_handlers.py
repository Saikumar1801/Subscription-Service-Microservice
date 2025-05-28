from flask import jsonify # We might use this later
# from pydantic import ValidationError # If using Pydantic for validation

# Custom error classes (to be defined more fully later)
class AppError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class NotFoundError(AppError):
    def __init__(self, resource_name="Resource"):
        super().__init__(f"{resource_name} not found", 404)


def register_error_handlers(app):
    @app.errorhandler(NotFoundError)
    def handle_not_found(error):
        response = jsonify({'error': error.message})
        response.status_code = error.status_code
        return response

    @app.errorhandler(AppError)
    def handle_app_error(error):
        response = jsonify({'error': error.message})
        response.status_code = error.status_code
        return response

    # Example for Pydantic validation errors if you integrate Flask-Pydantic or manual validation
    # @app.errorhandler(ValidationError)
    # def handle_validation_error(error):
    #     return jsonify({"error": "Validation Error", "details": error.errors()}), 400

    @app.errorhandler(404) # Flask's built-in 404
    def handle_flask_not_found(error):
        return jsonify({'error': 'Endpoint not found', 'message': str(error)}), 404

    @app.errorhandler(500) # Flask's built-in 500
    def handle_flask_internal_error(error):
        app.logger.error(f"Unhandled Internal Server Error: {error}", exc_info=True)
        return jsonify({'error': 'Internal Server Error', 'message': "An unexpected error occurred."}), 500

    app.logger.info("Custom error handlers registered.")