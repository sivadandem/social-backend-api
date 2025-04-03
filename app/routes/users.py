# app/routes/users.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, FriendRequest, FriendRequestStatus, db
from ..schemas import user_profile_schema, user_public_schema, users_public_schema, user_update_schema
from ..utils.helpers import error_response, success_response
from marshmallow import ValidationError
from sqlalchemy import or_, and_, not_, func # Import func for RAND()
import random

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return error_response("User not found.", 404) # Should not happen if JWT is valid

    return success_response(user_profile_schema.dump(user), 200)

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return error_response("User not found.", 404)

    try:
        # Use partial=True to allow partial updates
        data = user_update_schema.load(request.json, partial=True)
    except ValidationError as err:
        return error_response(err.messages, 400)

    if 'name' in data:
        user.name = data['name']
    if 'bio' in data:
        user.bio = data['bio']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Log error e
        return error_response("Failed to update profile.", 500)

    return success_response(user_profile_schema.dump(user), 200)


@users_bp.route('/', methods=['GET'])
@jwt_required()
def list_users():
    current_user_id = get_jwt_identity()

    # --- Filtering for Search (Bonus) ---
    search_query = request.args.get('search', None)

    query = User.query.filter(User.id != current_user_id)

    if search_query:
        query = query.filter(User.name.ilike(f"%{search_query}%")) # Case-insensitive search

    # --- Pagination (Bonus) ---
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int) # Default 10 users per page
    paginated_users = query.paginate(page=page, per_page=per_page, error_out=False)

    users = paginated_users.items
    result = users_public_schema.dump(users)

    return success_response({
        "users": result,
        "total": paginated_users.total,
        "pages": paginated_users.pages,
        "current_page": paginated_users.page,
        "per_page": paginated_users.per_page,
        "has_next": paginated_users.has_next,
        "has_prev": paginated_users.has_prev
    }, 200)


@users_bp.route('/suggestions', methods=['GET'])
@jwt_required()
def get_suggestions():
    current_user_id = get_jwt_identity()
    limit = 5 # Suggest 5 users

    # 1. Find IDs of current friends
    friends1 = db.session.query(FriendRequest.recipient_id).filter(
        FriendRequest.requester_id == current_user_id,
        FriendRequest.status == FriendRequestStatus.ACCEPTED
    )
    friends2 = db.session.query(FriendRequest.requester_id).filter(
        FriendRequest.recipient_id == current_user_id,
        FriendRequest.status == FriendRequestStatus.ACCEPTED
    )
    friend_ids = {row[0] for row in friends1.union(friends2).all()} # Use set for efficiency

    # 2. Find IDs of users with pending requests (sent or received)
    pending1 = db.session.query(FriendRequest.recipient_id).filter(
        FriendRequest.requester_id == current_user_id,
        FriendRequest.status == FriendRequestStatus.PENDING
    )
    pending2 = db.session.query(FriendRequest.requester_id).filter(
        FriendRequest.recipient_id == current_user_id,
        FriendRequest.status == FriendRequestStatus.PENDING
    )
    pending_ids = {row[0] for row in pending1.union(pending2).all()}

    # 3. Combine excluded IDs (self + friends + pending)
    exclude_ids = friend_ids.union(pending_ids)
    exclude_ids.add(current_user_id)

    # 4. Query for users excluding the excluded IDs, order randomly and limit
    # Using func.rand() for MySQL. For PostgreSQL use func.random().
    # Be aware: RAND()/random() can be slow on large tables.
    # Alternative: Fetch more users than needed and use random.sample in Python.
    suggested_users = User.query.filter(
        not_(User.id.in_(list(exclude_ids)))
    ).order_by(func.rand()).limit(limit).all()

    # Fallback if not enough random users found (e.g., very small user base)
    if len(suggested_users) < limit:
         # Fetch any users not excluded, limit again
         additional_users = User.query.filter(
             not_(User.id.in_(list(exclude_ids)))
         ).limit(limit).all()
         # Simple merge and take unique up to limit (less random)
         seen_ids = {u.id for u in suggested_users}
         for u in additional_users:
             if len(suggested_users) >= limit: break
             if u.id not in seen_ids:
                 suggested_users.append(u)
                 seen_ids.add(u.id)


    return success_response(users_public_schema.dump(suggested_users), 200)