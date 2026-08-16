from database import db


class Classroom(db.Model):
    __tablename__ = "classrooms"

    classroom_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    classroom_name = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    camera_source = db.Column(
        db.String(255),
        nullable=True
    )

    capacity = db.Column(
        db.Integer,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="ACTIVE",
        nullable=False
    )

    def __repr__(self):
        return f"<Classroom {self.classroom_name}>"