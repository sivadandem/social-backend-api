# app/__init__.py
from flask import Flask
from .config import Config
from .extensions import db, migrate, ma, jwt
from .models import User # Import models to ensure they are known to SQLAlchemy/Migrate

def create_app(config_class=Config):
    #print("--- Creating Flask app instance ---")
    app = Flask(__name__)
    #print(f"--- Applying config from: {config_class} ---")
    app.config.from_object(config_class)

    # Print the DEBUG value *after* loading the config object
    #print(f"--- app.config['DEBUG'] after from_object: {app.config.get('DEBUG')} ---")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db) # Initialize Flask-Migrate
    ma.init_app(app)
    jwt.init_app(app)

    # ... JWT user lookup loader ...

    # Register Blueprints
    from .routes.auth import auth_bp
    from .routes.users import users_bp
    from .routes.friends import friends_bp
    from .errors import errors_bp # Import error handlers blueprint

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(errors_bp) # Register error handlers

    #print(f"--- Final app.config['DEBUG'] before return: {app.config.get('DEBUG')} ---")
    #print("--- Finished creating Flask app instance ---")
    return app