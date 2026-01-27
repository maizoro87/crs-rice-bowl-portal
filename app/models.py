"""
Database models for the CRS Rice Bowl application.
"""
from datetime import datetime
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for admin authentication."""

    __tablename__ = 'users'

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash: str = db.Column(db.String(255), nullable=False)
    created_at: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        """
        Hash and set the user's password.

        Args:
            password: Plain text password to hash
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username}>'


class Quiz(db.Model):
    """Quiz model for weekly country trivia challenges."""

    __tablename__ = 'quizzes'

    id: int = db.Column(db.Integer, primary_key=True)
    week_number: int = db.Column(db.Integer, nullable=False, unique=True, index=True)
    country_name: str = db.Column(db.String(100), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    forms_link: str = db.Column(db.String(500), nullable=True)
    opens_at: datetime = db.Column(db.DateTime, nullable=True)
    closes_at: datetime = db.Column(db.DateTime, nullable=True)
    schedule_mode: str = db.Column(db.String(20), nullable=False, default='manual')  # 'manual' or 'scheduled'
    manual_visible: bool = db.Column(db.Boolean, nullable=False, default=False)
    participant_count: int = db.Column(db.Integer, nullable=False, default=0)
    participants_text: str = db.Column(db.Text, nullable=True)  # Comma-separated names
    winner_1: Optional[str] = db.Column(db.String(200), nullable=True)
    winner_2: Optional[str] = db.Column(db.String(200), nullable=True)
    winner_3: Optional[str] = db.Column(db.String(200), nullable=True)
    created_at: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_visible(self) -> bool:
        """
        Determine if quiz is currently visible based on schedule mode.

        Returns:
            True if quiz should be displayed, False otherwise
        """
        if self.schedule_mode == 'manual':
            return self.manual_visible
        elif self.schedule_mode == 'scheduled':
            now = datetime.utcnow()
            if self.opens_at and self.closes_at:
                return self.opens_at <= now <= self.closes_at
            return False
        return False

    def __repr__(self) -> str:
        return f'<Quiz Week {self.week_number}: {self.country_name}>'


class SchoolClass(db.Model):
    """School class model for tracking Rice Bowl donations."""

    __tablename__ = 'school_classes'

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False, unique=True, index=True)
    rice_bowl_amount: float = db.Column(db.Float, nullable=False, default=0.0)
    created_at: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<SchoolClass {self.name}: ${self.rice_bowl_amount:.2f}>'


class Setting(db.Model):
    """Key-value store for application settings."""

    __tablename__ = 'settings'

    key: str = db.Column(db.String(100), primary_key=True)
    value: str = db.Column(db.Text, nullable=True)

    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a setting value by key.

        Args:
            key: Setting key to retrieve
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        setting = Setting.query.get(key)
        return setting.value if setting else default

    @staticmethod
    def set(key: str, value: str) -> None:
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        setting = Setting.query.get(key)
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.session.add(setting)
        db.session.commit()

    def __repr__(self) -> str:
        return f'<Setting {self.key}={self.value}>'


class Announcement(db.Model):
    """Announcement model for homepage banners."""

    __tablename__ = 'announcements'

    id: int = db.Column(db.Integer, primary_key=True)
    text: str = db.Column(db.Text, nullable=False)
    start_at: datetime = db.Column(db.DateTime, nullable=True)
    end_at: datetime = db.Column(db.DateTime, nullable=True)
    enabled: bool = db.Column(db.Boolean, nullable=False, default=True)
    created_at: datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def is_active(self) -> bool:
        """
        Determine if announcement is currently active.

        Returns:
            True if announcement should be displayed, False otherwise
        """
        if not self.enabled:
            return False

        now = datetime.utcnow()

        # If no time restrictions, enabled=True means active
        if not self.start_at and not self.end_at:
            return True

        # Check time window
        if self.start_at and now < self.start_at:
            return False
        if self.end_at and now > self.end_at:
            return False

        return True

    def __repr__(self) -> str:
        return f'<Announcement {self.id}: {self.text[:50]}...>'
