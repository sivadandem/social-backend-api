# app/routes/auth.py
from flask import Blueprint, request, jsonify
from ..models import User, db
from ..schemas import user_register_schema, user_login_schema, user_profile_schema
from ..utils.helpers import error_response, success_response
from flask_jwt_extended import create_access_token
from marshmallow import ValidationError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = user_register_schema.load(request.json)
    except ValidationError as err:
        return error_response(err.messages, 400)

    # Check if email already exists (handled by DB unique constraint + error handler now)
    # if User.query.filter_by(email=data['email']).first():
    #     return error_response({"email": ["Email already registered."]}, 409) # 409 Conflict

    new_user = User(name=data['name'], email=data['email'])
    new_user.set_password(data['password'])

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e: # Catch potential DB errors during commit
        db.session.rollback()
        # Log the error e
        return error_response("Failed to register user due to a database error.", 500)


    # Exclude password from the response
    user_data = user_profile_schema.dump(new_user)
    return success_response({"message": "User registered successfully", "user": user_data}, 201)


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = user_login_schema.load(request.json)
    except ValidationError as err:
        return error_response(err.messages, 400)

    user = User.query.filter_by(email=data['email']).first()

    if user and user.check_password(data['password']):
        # --- CHANGE HERE: Convert user.id to string ---
        identity_str = str(user.id)
        access_token = create_access_token(identity=identity_str)
        # --- END CHANGE ---
        return success_response({'access_token': access_token}, 200)
    else:
        return error_response("Invalid email or password.", 401)

# TODO: Add Google Authentication routes if implementing
# /auth/google (initiates flow)
# /auth/google/callback (handles response from Google)