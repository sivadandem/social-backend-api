# app/schemas.py
from .extensions import ma
from .models import User, FriendRequest, FriendRequestStatus
from marshmallow import fields, validate, ValidationError

# Basic schema for user data visible publicly or to other users
class UserPublicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        # Exclude sensitive or internal fields
        exclude = ("password_hash", "updated_at", "sent_requests", "received_requests")

# Schema for current user's profile (can include more details)
class UserProfileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = ("password_hash", "sent_requests", "received_requests") # Keep created_at/updated_at

# Schema for user registration
class UserRegisterSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=80))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6)) # Basic password length validation

# Schema for user login
class UserLoginSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)

# Schema for updating user profile
class UserUpdateSchema(ma.Schema):
    name = fields.String(validate=validate.Length(min=1, max=80))
    bio = fields.String(allow_none=True) # Allow setting bio to null/empty

# Schema for displaying friend requests (showing user details)
class FriendRequestSchema(ma.SQLAlchemyAutoSchema):
    requester = fields.Nested(UserPublicSchema, only=("id", "name", "email"))
    recipient = fields.Nested(UserPublicSchema, only=("id", "name", "email"))
    status = fields.Method("get_status_string", deserialize="load_status_string") # Use string representation

    class Meta:
        model = FriendRequest
        load_instance = True
        include_fk = True # Include requester_id and recipient_id if needed

    def get_status_string(self, obj):
        return obj.status.value # Return 'pending', 'accepted', 'rejected'

    def load_status_string(self, value):
        try:
            return FriendRequestStatus(value)
        except ValueError:
            raise ValidationError(f"Invalid status value: {value}. Must be one of: {[s.value for s in FriendRequestStatus]}")

# Instantiate schemas
user_public_schema = UserPublicSchema()
users_public_schema = UserPublicSchema(many=True)
user_profile_schema = UserProfileSchema()
user_register_schema = UserRegisterSchema()
user_login_schema = UserLoginSchema()
user_update_schema = UserUpdateSchema()
friend_request_schema = FriendRequestSchema()
friend_requests_schema = FriendRequestSchema(many=True)