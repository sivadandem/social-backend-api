# app/routes/friends.py
from flask import Blueprint, request, jsonify, current_app # Import current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, FriendRequest, FriendRequestStatus, db
from ..schemas import friend_request_schema, friend_requests_schema, users_public_schema
from ..utils.helpers import error_response, success_response
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
import logging # Import logging

friends_bp = Blueprint('friends', __name__, url_prefix='/friend-requests')

# Configure basic logging if not already done elsewhere (e.g., in create_app)
# This ensures INFO messages appear on the console if Flask's default level is higher
# You might move this to your app factory (__init__.py) for better structure
logging.basicConfig(level=logging.INFO)


@friends_bp.route('/send/<int:recipient_id>', methods=['POST'])
@jwt_required()
def send_friend_request(recipient_id):
    # --- Convert JWT identity (string) to integer for comparison/DB use ---
    try:
        requester_id_str = get_jwt_identity()
        requester_id = int(requester_id_str)
    except (ValueError, TypeError):
         current_app.logger.error(f"Invalid JWT identity format: {requester_id_str}")
         # You might want a more specific error response here
         return error_response("Invalid user identity in token.", 400)
    # --- End conversion ---

    # Prevent sending request to self (comparing integers)
    if requester_id == recipient_id:
        return error_response("Cannot send friend request to yourself.", 400)

    recipient = User.query.get(recipient_id)
    if not recipient:
        return error_response("Recipient user not found.", 404)

    # Check if a request already exists (in either direction) or they are already friends
    # Ensure comparisons use integer IDs
    existing_request = FriendRequest.query.filter(
        or_(
            and_(FriendRequest.requester_id == requester_id, FriendRequest.recipient_id == recipient_id),
            and_(FriendRequest.requester_id == recipient_id, FriendRequest.recipient_id == requester_id)
        )
    ).first()

    if existing_request:
        if existing_request.status == FriendRequestStatus.ACCEPTED:
             return error_response("You are already friends with this user.", 409) # 409 Conflict
        elif existing_request.status == FriendRequestStatus.PENDING:
             # Check who sent the existing pending request
             if existing_request.requester_id == requester_id:
                 return error_response("Friend request already sent and is pending.", 409)
             else:
                 return error_response("This user has already sent you a friend request. Please accept or reject it.", 409)
        elif existing_request.status == FriendRequestStatus.REJECTED:
             # Re-sending after rejection: delete old one, create new pending one.
             db.session.delete(existing_request)
             # Fall through to create the new request...

    # Create using integer IDs
    new_request = FriendRequest(requester_id=requester_id, recipient_id=recipient_id, status=FriendRequestStatus.PENDING)

    try:
        db.session.add(new_request)
        db.session.commit()
        # Use schema to return consistent output
        return success_response({"message": "Friend request sent successfully.", "request": friend_request_schema.dump(new_request)}, 201)
    except IntegrityError as e: # Catch potential unique constraint violation
         db.session.rollback()
         # Check if it's the specific unique constraint error
         # Note: Error message structure might vary slightly between DBs/versions
         if "uq_friend_request_pair" in str(e.orig) or "Duplicate entry" in str(e.orig):
             return error_response({"request": ["Friend request relationship already exists or is pending."]}, 409)
         else:
             current_app.logger.error(f"Database integrity error sending request from {requester_id} to {recipient_id}. Error: {e}", exc_info=True)
             return error_response("Database error occurred while sending request.", 500)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to send friend request from {requester_id} to {recipient_id}. Error: {e}", exc_info=True)
        return error_response("Failed to send friend request.", 500)


@friends_bp.route('/<int:request_id>/accept', methods=['PUT'])
@jwt_required()
def accept_friend_request(request_id):
    current_user_identity = get_jwt_identity() # Get raw string identity from token
    current_app.logger.info(f"--- Attempting to accept request_id: {request_id}")
    current_app.logger.info(f"--- JWT Identity (sub claim): '{current_user_identity}' (type: {type(current_user_identity)})")

    try:
        # Convert the string identity from JWT to an integer for comparison
        current_user_id = int(current_user_identity)
        current_app.logger.info(f"--- Converted current_user_id to int: {current_user_id} (type: {type(current_user_id)})")
    except (ValueError, TypeError):
        # Handle cases where JWT sub is not a valid integer string
        current_app.logger.error(f"--- Failed to convert JWT identity '{current_user_identity}' to int.")
        return error_response("Invalid user identity in token.", 400)


    friend_request = FriendRequest.query.get(request_id) # Fetch by primary key

    if not friend_request:
        current_app.logger.warning(f"--- Friend request with id {request_id} not found.")
        return error_response("Friend request not found.", 404)

    # --- CRITICAL LOGGING ---
    # Log the types and values being compared
    current_app.logger.info(f"--- Found friend_request.id: {friend_request.id}")
    current_app.logger.info(f"--- Friend_request.recipient_id from DB: {friend_request.recipient_id} (type: {type(friend_request.recipient_id)})")
    current_app.logger.info(f"--- Current_user_id from token (as int): {current_user_id} (type: {type(current_user_id)})")
    current_app.logger.info(f"--- Checking authorization condition: friend_request.recipient_id ({friend_request.recipient_id}) != current_user_id ({current_user_id})")
    # --- END CRITICAL LOGGING ---

    # Compare integer values
    if friend_request.recipient_id != current_user_id:
        current_app.logger.warning(f"--- AUTHORIZATION FAILED: User {current_user_id} cannot accept request {request_id} intended for user {friend_request.recipient_id}.")
        return error_response("You are not authorized to respond to this request.", 403)

    # Check if the request is actually pending
    if friend_request.status != FriendRequestStatus.PENDING:
        current_app.logger.warning(f"--- Request {request_id} is not pending (status: {friend_request.status.value}). Cannot accept.")
        return error_response(f"Request is not pending (status: {friend_request.status.value}).", 400)

    friend_request.status = FriendRequestStatus.ACCEPTED
    try:
        db.session.commit()
        current_app.logger.info(f"--- Successfully accepted request {request_id} by user {current_user_id}.")
        return success_response({"message": "Friend request accepted.", "request": friend_request_schema.dump(friend_request)}, 200)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"--- Database error committing acceptance for request {request_id}. Error: {e}", exc_info=True)
        return error_response("Failed to accept friend request.", 500)


@friends_bp.route('/<int:request_id>/reject', methods=['PUT'])
@jwt_required()
def reject_friend_request(request_id):
    # --- Convert JWT identity (string) to integer ---
    try:
        current_user_identity = get_jwt_identity()
        current_user_id = int(current_user_identity)
    except (ValueError, TypeError):
         current_app.logger.error(f"Invalid JWT identity format: {current_user_identity}")
         return error_response("Invalid user identity in token.", 400)
    # --- End conversion ---

    friend_request = FriendRequest.query.get(request_id)

    if not friend_request:
        return error_response("Friend request not found.", 404)

    # Compare integer values
    if friend_request.recipient_id != current_user_id:
        return error_response("You are not authorized to respond to this request.", 403)

    if friend_request.status != FriendRequestStatus.PENDING:
        return error_response(f"Request is not pending (status: {friend_request.status.value}).", 400)

    friend_request.status = FriendRequestStatus.REJECTED
    try:
        # Optionally, you could delete the rejected request immediately or later
        # db.session.delete(friend_request)
        db.session.commit()
        current_app.logger.info(f"--- Successfully rejected request {request_id} by user {current_user_id}.")
        return success_response({"message": "Friend request rejected.", "request": friend_request_schema.dump(friend_request)}, 200)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"--- Database error committing rejection for request {request_id}. Error: {e}", exc_info=True)
        return error_response("Failed to reject friend request.", 500)


@friends_bp.route('/incoming', methods=['GET'])
@jwt_required()
def list_incoming_requests():
    # --- Convert JWT identity (string) to integer ---
    try:
        current_user_identity = get_jwt_identity()
        current_user_id = int(current_user_identity)
    except (ValueError, TypeError):
         current_app.logger.error(f"Invalid JWT identity format: {current_user_identity}")
         return error_response("Invalid user identity in token.", 400)
    # --- End conversion ---

    # Filter using integer ID
    incoming_requests = FriendRequest.query.filter(
        FriendRequest.recipient_id == current_user_id,
        FriendRequest.status == FriendRequestStatus.PENDING
    ).order_by(FriendRequest.created_at.desc()).all()

    return success_response(friend_requests_schema.dump(incoming_requests), 200)


@friends_bp.route('/list', methods=['GET'])
@jwt_required()
def list_friends():
    # --- Convert JWT identity (string) to integer ---
    try:
        current_user_identity = get_jwt_identity()
        current_user_id = int(current_user_identity)
    except (ValueError, TypeError):
         current_app.logger.error(f"Invalid JWT identity format: {current_user_identity}")
         return error_response("Invalid user identity in token.", 400)
    # --- End conversion ---

    # Find accepted requests where the current user (as integer ID) is requester or recipient
    accepted_requests = FriendRequest.query.filter(
        FriendRequest.status == FriendRequestStatus.ACCEPTED,
        or_(
            FriendRequest.requester_id == current_user_id,
            FriendRequest.recipient_id == current_user_id
        )
    ).all()

    friend_ids = set()
    for req in accepted_requests:
        if req.requester_id == current_user_id:
            friend_ids.add(req.recipient_id)
        else:
            friend_ids.add(req.requester_id)

    if not friend_ids:
        return success_response({"friends": []}, 200)

    # Fetch friend user objects using the set of integer IDs
    friends = User.query.filter(User.id.in_(list(friend_ids))).all()

    return success_response({"friends": users_public_schema.dump(friends)}, 200)