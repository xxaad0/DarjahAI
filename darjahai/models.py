from flask_login import UserMixin
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from .extensions import db, bcrypt

from sqlalchemy import UniqueConstraint

from datetime import datetime, timezone, date

import uuid



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    fullname = db.Column(db.String(50), nullable=False)

    email_verified = db.Column(db.Boolean, default=False, nullable=False)

    character = db.relationship("Character", backref="user", uselist=False)

    plan= db.Column(db.String(20),nullable=False,default="free")

    stripeCustomerID= db.Column(db.String(255),nullable=True)
    stripeSuscriptionID=db.Column(db.String(255),nullable=True)
    stripeStatus= db.Column(db.String(255),nullable=True)

    dayCount= db.Column(db.Integer,nullable=False,default=0)
    dayBegin= db.Column(db.Date,nullable=True)

    monthCount= db.Column(db.Integer,nullable=False,default=0)
    monthStart = db.Column(db.Date,nullable=True)

    def set_password(self, raw_password: str) -> None:
        self.password = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def generate_reset_password_token(self) -> str:
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps(self.email, salt=current_app.config["RESET_PASS_SALT"])

    def generate_verify_email_token(self) -> str:
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps(self.email, salt=current_app.config["EMAIL_VERIFICATION_SALT"])

    @staticmethod
    def verify_verification_token(token: str, user_id: int):
        user = db.session.get(User, user_id)
        if user is None:
            return None

        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            token_email = s.loads(
                token,
                max_age=current_app.config["EMAIL_VERIFICATION_TOKEN_MAX_AGE"],
                salt=current_app.config["EMAIL_VERIFICATION_SALT"],
            )
        except (BadSignature, SignatureExpired):
            return None

        return user if token_email == user.email else None

    @staticmethod
    def validate_reset_password_token(token: str, user_id: int):
        user = db.session.get(User, user_id)
        if user is None:
            return None

        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            token_email = s.loads(
                token,
                max_age=current_app.config["RESET_PASS_TOKEN_MAX_AGE"],
                salt=current_app.config["RESET_PASS_SALT"],
            )
        except (BadSignature, SignatureExpired):
            return None

        return user if token_email == user.email else None


class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    c_name = db.Column(db.String(20), nullable=False)
    c_class = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)

    level= db.Column(db.Integer,nullable=False,default=1)
    xp_total = db.Column(db.Integer,nullable=False,default=0)
    xpforlevel= db.Column(db.Integer,nullable=False,default=0)

    lastdateactive= db.Column(db.Date,nullable=True)
    dailystreak= db.Column(db.Integer,nullable=False,default=0)
    beststreak= db.Column(db.Integer,nullable=False,default=0)
    activedaystotal= db.Column(db.Integer,nullable=False,default=0)



    
    created_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


    
class XPSTAT(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   c_id = db.Column(db.Integer, db.ForeignKey("character.id"), nullable=False,index=True)
   amount = db.Column(db.Integer, nullable=False)
   reason = db.Column(db.String,nullable=False)
   created_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
   
   character = db.relationship("Character", backref=db.backref("xp_stats", lazy=True))


class Tasks(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    task_name=db.Column(db.String(20),nullable=False)
    task_id=db.Column(db.String(20),nullable=False)
    task_category=db.Column(db.String(20),nullable=False)
    task_status=db.Column(db.String(20),nullable=False)
    task_priority=db.Column(db.String(20),nullable=False)
    task_description=db.Column(db.String(300),nullable=False)
    task_location=db.Column(db.String(20),nullable=False)
    task_due_date_entered=db.Column(db.String(20),nullable=False)

    task_reminder_status =db.Column(db.String(20),nullable=False,default="ON")


    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("user_id","task_id",name="uq_tasks_user_task_id"),
        UniqueConstraint("user_id","task_name",name="uq_tasks_user_task_name"),

    )

    user= db.relationship("User",backref=db.backref("tasks",lazy=True))

    subtasks = db.relationship(
        "SubTasks",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True
    )

    task_date_created= db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class SubTasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    subtask_name = db.Column(db.String(20), nullable=False)
    subtask_id = db.Column(db.String(20), nullable=False)
    subtask_category = db.Column(db.String(20), nullable=False)
    subtask_status = db.Column(db.String(20), nullable=False)
    subtask_priority = db.Column(db.String(20), nullable=False)
    subtask_description = db.Column(db.String(300), nullable=False)
    subtask_location = db.Column(db.String(20), nullable=False)
    subtask_due_date_entered = db.Column(db.String(20), nullable=False)

    subtask_reminder_status = db.Column(db.String(20), nullable=False, default="ON")

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    task_id= db.Column(
        db.Integer,
        db.ForeignKey("tasks.id",ondelete="CASCADE"),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "subtask_id", name="uq_subtasks_user_subtask_id"),
        UniqueConstraint("user_id", "subtask_name", name="uq_subtasks_user_subtask_name"),
    )

    user = db.relationship("User", backref=db.backref("subtasks", lazy=True))
    task = db.relationship("Tasks",back_populates="subtasks")



    subtask_date_created = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class TaskTopTerm(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id  =  db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    task_term= db.Column(db.String(500),nullable=False)
    task_score = db.Column(db.Float,nullable=False)

    task_computed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    task_version = db.Column(db.String(50),nullable=False,default=lambda: str(uuid.uuid4()))
    
    __table_args__ = (
        UniqueConstraint("user_id", "task_term","task_version", name="uq_tasktopterm_user_task_term_task_version"),
    )

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False,index=True)
    title = db.Column(db.String(100),nullable=False,default="New chat")
    created_date = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_date = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    summary= db.Column(db.String(200),nullable=True)

    messages = db.relationship(
        "ChatMessages",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True,
    )

class ChatMessages(db.Model):
    id= db.Column(db.Integer,primary_key=True)
    session_id=db.Column(db.Integer,db.ForeignKey("chat_session.id",ondelete="CASCADE"),nullable=False,index=True)
    role= db.Column(db.String(20),nullable=False)
    content= db.Column(db.Text,nullable=False)
    created_date = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    session = db.relationship("ChatSession", back_populates="messages")



