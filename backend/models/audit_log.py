from database import db
from datetime import datetime


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    log_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        nullable=True
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    table_name = db.Column(
        db.String(100),
        nullable=True
    )

    old_value = db.Column(
        db.Text,
        nullable=True
    )

    new_value = db.Column(
        db.Text,
        nullable=True
    )

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<AuditLog {self.action}>"