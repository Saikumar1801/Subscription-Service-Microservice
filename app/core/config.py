import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=dotenv_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-default-fallback-secret-key-if-not-set'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = FLASK_ENV == 'development'

    MONGODB_SETTINGS = {
        'host': os.environ.get('MONGODB_SETTINGS_HOST'),
    }
    if not MONGODB_SETTINGS.get('host'):
        print("WARNING: MONGODB_SETTINGS_HOST is not set in the environment!")

    JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
    SCHEDULER_API_ENABLED = os.environ.get('SCHEDULER_API_ENABLED', 'True').lower() == 'true'
    
    # MONGODB_SETTINGS_HOST should be your Atlas SRV string
    # MONGODB_SCHEDULER_DB = os.environ.get('MONGODB_SCHEDULER_DB', 'scheduler_jobs_db') # Or use main DB
    # SCHEDULER_JOBSTORES = {
    #    'default': {'type': 'mongodb', 'host': MONGODB_SETTINGS_HOST, 'database': MONGODB_SCHEDULER_DB}
    # }
    # SCHEDULER_EXECUTORS = {
    #    'default': {'type': 'threadpool', 'max_workers': 10} # Default is 10
    # }
    # SCHEDULER_JOB_DEFAULTS = {
    #    'coalesce': True, # Ensures only one instance of a job runs if multiple are scheduled close together
    #    'max_instances': 1 # Crucial for preventing multiple instances of the same job running concurrently across scaled app servers
    # }