from flask_mongoengine import MongoEngine

db = MongoEngine()

def init_db(app):
    db.init_app(app)
    app.logger.info("MongoEngine initialized with Flask app.")