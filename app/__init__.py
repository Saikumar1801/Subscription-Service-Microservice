import os
from flask import Flask, jsonify
from flask_apscheduler import APScheduler
import pymongo

from app.core.config import Config
from app.core.database import db, init_db

scheduler = APScheduler()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize MongoEngine
    init_db(app)

    # Initialize APScheduler if enabled
    if app.config.get("SCHEDULER_API_ENABLED", False):
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or app.config.get("FLASK_ENV") != "development":
            if not scheduler.running:
                try:
                    scheduler.init_app(app)
                    from app.tasks import expiration_checker  # noqa: F401
                    scheduler.start()
                    app.logger.info("APScheduler initialized and started.")
                except Exception as e:
                    app.logger.error(f"Failed to initialize or start APScheduler: {e}")
            else:
                app.logger.info("APScheduler already running (likely in main process).")
        else:
            app.logger.info("APScheduler setup skipped in Werkzeug reloader child process.")
    else:
        app.logger.info("APScheduler is disabled via config.")

    # Register Blueprints
    from app.api.subscriptions_api import subscriptions_bp
    from app.api.plans_api import plans_bp
    app.register_blueprint(subscriptions_bp, url_prefix='/api')
    app.register_blueprint(plans_bp, url_prefix='/api')
    app.logger.info("Blueprints registered.")

    # Register Error Handlers
    from app.utils import error_handlers
    error_handlers.register_error_handlers(app)
    app.logger.info("Error handlers registered.")

    # Import models
    from app.models import plan, subscription  # noqa: F401
    app.logger.info("Models module imported.")

    # Health check endpoint
    @app.route('/health')
    def health_check():
        db_status = "DB Not Connected or Check Failed"
        db_name_str = ""
        scheduler_status = "Scheduler Not Initialized or Not Running"
        http_status_code = 503

        try:
            if db.connection:
                admin_db = db.connection.admin
                admin_db.command('ping')

                default_db_name = db.connection.get_default_database().name
                db_name_str = f" (Default DB: {default_db_name})"
                db_status = "DB Connected"
                http_status_code = 200
            else:
                db_status = "DB Connection object not available"

            if scheduler:
                if app.config.get("SCHEDULER_API_ENABLED", False):
                    scheduler_status = "Scheduler running" if scheduler.running else "Scheduler initialized but not running"
                else:
                    scheduler_status = "Scheduler disabled by config"
            else:
                scheduler_status = "Scheduler object not found"

        except pymongo.errors.ConnectionFailure as e:
            app.logger.error(f"Health check DB connection failure: {e}")
            db_status = "DB Connection Failure"
            http_status_code = 503
        except pymongo.errors.PyMongoError as e:
            app.logger.error(f"Health check DB PyMongo error: {e}")
            db_status = f"DB Error ({type(e).__name__})"
            http_status_code = 503
        except Exception as e:
            app.logger.error(f"Health check failed with unexpected error: {e}, Type: {type(e)}")
            db_status = "Unexpected Error during health check"
            http_status_code = 503

        final_status_message = f"Status: {'OK' if http_status_code == 200 else 'ERROR'}"
        final_status_message += f" - {db_status}{db_name_str}"
        final_status_message += f" - {scheduler_status}"
        return final_status_message, http_status_code

    # --- TEST TOKEN ENDPOINT (FOR DEBUG MODE ONLY) ---
    if app.debug:
        from app.core.security import generate_token

        @app.route('/get-token/<user_id_for_token>', methods=['GET'])
        def get_test_token(user_id_for_token):
            try:
                token = generate_token(user_id=user_id_for_token)
                return jsonify(access_token=token, user_id=user_id_for_token), 200
            except ValueError as e:
                return jsonify(error=str(e)), 500
            except Exception as e:
                app.logger.error(f"Error generating test token: {e}")
                return jsonify(error="Failed to generate token"), 500

    # Final logs
    app.logger.info(f"Flask app created with env: {app.config.get('FLASK_ENV')}")
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        app.logger.info("Running in Werkzeug main process.")

    return app
