from database import db
from datetime import date


class Session(db.Model):
    __tablename__ = "sessions"

    session_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    classroom_id = db.Column(
        db.Integer,
        db.ForeignKey("classrooms.classroom_id"),
        nullable=False
    )

    period_number = db.Column(
        db.Integer,
        nullable=False
    )

    date = db.Column(
        db.Date,
        default=date.today,
        nullable=False
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="SCHEDULED",
        nullable=False
    )

    classroom = db.relationship(
        "Classroom",
        backref=db.backref("sessions", lazy=True)
    )

    def __repr__(self):
        return (
            f"<Session Classroom={self.classroom_id} "
            f"Period={self.period_number} "
            f"Date={self.date}>"
        )