from database import db
from datetime import datetime


class Attendance(db.Model):
    __tablename__ = "attendance"

    attendance_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.student_id"),
        nullable=False
    )

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("sessions.session_id"),
        nullable=False
    )

    detected_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    confidence = db.Column(
        db.Float,
        nullable=True
    )

    liveness_score = db.Column(
        db.Float,
        nullable=True
    )

    embedding_distance = db.Column(
        db.Float,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="PRESENT",
        nullable=False
    )

    marked_by = db.Column(
        db.String(30),
        default="SYSTEM",
        nullable=False
    )

    notes = db.Column(
        db.String(255),
        nullable=True
    )

    student = db.relationship(
        "Student",
        backref=db.backref("attendance_records", lazy=True)
    )

    session = db.relationship(
        "Session",
        backref=db.backref("attendance_records", lazy=True)
    )

    def __repr__(self):
        return (
            f"<Attendance Student={self.student_id} "
            f"Session={self.session_id} "
            f"Status={self.status}>"
        )