# app/models.py
from .extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint, UniqueConstraint, Index, func # Import func for RAND()

# Enum definition (works with SQLAlchemy >= 1.x, may need adjustment for older versions)
import enum
class FriendRequestStatus(enum.Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships for friend requests
    sent_requests = db.relationship('FriendRequest', foreign_keys='FriendRequest.requester_id', backref='requester', lazy='dynamic')
    received_requests = db.relationship('FriendRequest', foreign_keys='FriendRequest.recipient_id', backref='recipient', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.name} ({self.email})>'


class FriendRequest(db.Model):
    __tablename__ = 'friend_requests'
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Enum(FriendRequestStatus), nullable=False, default=FriendRequestStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint('requester_id != recipient_id', name='check_not_self_request'),
        UniqueConstraint('requester_id', 'recipient_id', name='uq_friend_request_pair'),
        # Index might be useful depending on query patterns
        Index('ix_friend_request_recipient_status', 'recipient_id', 'status'),
    )

    def __repr__(self):
        return f'<FriendRequest {self.requester_id} -> {self.recipient_id} ({self.status.name})>'