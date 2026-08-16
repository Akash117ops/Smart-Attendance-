from database import db
from datetime import datetime


class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    usn = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)

    enrollment_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    status = db.Column(
        db.String(20),
        default="ACTIVE",
        nullable=False
    )

    # Face embedding will be stored here later.
    # We are keeping it as binary data because
    # DeepFace embeddings are numerical vectors.
    face_embedding = db.Column(db.LargeBinary, nullable=True)

    def __repr__(self):
        return f"<Student {self.usn} - {self.name}>"