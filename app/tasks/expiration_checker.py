from flask import current_app
from app import scheduler, create_app # Import create_app
from app.services.subscription_service import SubscriptionService
from datetime import datetime

@scheduler.task('interval', id='expire_subscriptions_job', seconds=30) # Test interval
# @scheduler.task('interval', id='expire_subscriptions_job', hours=1) # Production interval
def expire_subscriptions_task():
    """
    Scheduled task to check for and expire subscriptions that are past their end_date.
    """
    # Attempt to use current_app, but if it's not available (e.g., in a separate thread
    # not managed by Flask's context stack), create a new app context.
    app = current_app._get_current_object() if current_app else None

    if not app:
        # If current_app is not available, create a new app instance for this task's context.
        # This ensures that the task can access app.config, extensions like db, etc.
        app = create_app() # Use your app factory
        if not app:
            # This should not happen if create_app is robust
            print(f"CRITICAL [{datetime.utcnow()}]: Task '{expire_subscriptions_task.__name__}' "
                  f"could not create an app instance. Cannot proceed.")
            return
        
        # Push an application context manually.
        # This is necessary because we are outside the normal Flask request lifecycle.
        with app.app_context():
            app.logger.info(
                f"Running scheduled task: '{expire_subscriptions_task.__name__}' (with manually created app context)"
            )
            try:
                sub_service = SubscriptionService() 
                sub_service.expire_all_due_subscriptions()
                app.logger.info(
                    f"Scheduled task '{expire_subscriptions_task.__name__}' completed successfully (manual context)."
                )
            except Exception as e:
                app.logger.error(
                    f"Error during scheduled task '{expire_subscriptions_task.__name__}' (manual context): {e}", 
                    exc_info=True
                )
    else:
        # If current_app was available, proceed as before (Flask-APScheduler might handle context)
        # The 'with current_app.app_context()' might be redundant if current_app implies context,
        # but it's harmless and explicit.
        with app.app_context(): # Or just current_app.app_context() if app is already current_app
            app.logger.info(
                f"Running scheduled task: '{expire_subscriptions_task.__name__}' (with existing app context)"
            )
            try:
                sub_service = SubscriptionService() 
                sub_service.expire_all_due_subscriptions()
                app.logger.info(
                    f"Scheduled task '{expire_subscriptions_task.__name__}' completed successfully (existing context)."
                )
            except Exception as e:
                app.logger.error(
                    f"Error during scheduled task '{expire_subscriptions_task.__name__}' (existing context): {e}", 
                    exc_info=True
                )