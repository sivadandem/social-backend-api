# app/errors.py
from flask import Blueprint, jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from .utils.helpers import error_response

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return error_response(err.messages, 400)

@errors_bp.app_errorhandler(IntegrityError)
def handle_database_integrity_error(err):
    # Log the error for debugging: current_app.logger.error(f"Database Integrity Error: {err}")
    # Provide a generic message to the user
    db.session.rollback() # Rollback the session to avoid leaving it in a broken state
    # Check specific constraints if needed (e.g., unique email)
    if "UNIQUE constraint failed: users.email" in str(err.orig) or \
       "Duplicate entry" in str(err.orig) and "for key 'users.email'" in str(err.orig): # MySQL specific
         return error_response({"email": ["Email address already exists."]}, 409) # 409 Conflict
    if "UNIQUE constraint failed: uq_friend_request_pair" in str(err.orig) or \
       "Duplicate entry" in str(err.orig) and "for key 'uq_friend_request_pair'" in str(err.orig): # MySQL specific
         return error_response({"request": ["Friend request already exists or is pending."]}, 409)

    return error_response("Database integrity error occurred.", 400)


@errors_bp.app_errorhandler(404)
def resource_not_found(err):
    return error_response("The requested resource was not found.", 404)

@errors_bp.app_errorhandler(401)
def unauthorized(err):
     return error_response("Authentication required.", 401)

@errors_bp.app_errorhandler(403)
def forbidden(err):
     return error_response("You do not have permission to access this resource.", 403)

@errors_bp.app_errorhandler(500)
def internal_server_error(err):
    # Log the error: current_app.logger.error(f"Internal Server Error: {err}")
    db.session.rollback() # Rollback in case of DB issues during the request
    return error_response("An internal server error occurred.", 500)

# Need to import db here, maybe pass app context or move db initialization
# For simplicity here, assuming db is accessible or move this handler registration to __init__.py
from .extensions import db