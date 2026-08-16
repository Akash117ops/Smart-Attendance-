from database import db


class Faculty(db.Model):
    __tablename__ = "faculty"

    faculty_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        default="FACULTY",
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default="ACTIVE",
        nullable=False
    )

    def __repr__(self):
        return f"<Faculty {self.email}>"