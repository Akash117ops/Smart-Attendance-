
from flask import Flask, request
from flask_cors import CORS
from config import Config
from database import db
from models import (
    Student,
    Classroom,
    Session,
    Attendance,
    Faculty,
    AuditLog
)
from face_service import generate_student_embedding
from recognition_service import recognize_face

from datetime import datetime, date, time

import os
import tempfile


def create_app():
    app = Flask(__name__)

    # =====================================================
    # CONFIGURATION
    # =====================================================

    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # =====================================================
    # HOME
    # =====================================================

    @app.route("/")
    def home():
        return {
            "project": "AI-Based Smart Attendance Management System",
            "status": "Backend and database are connected",
            "version": "1.0"
        }

    # =====================================================
    # GET ALL STUDENTS
    # =====================================================

    @app.route("/api/students", methods=["GET"])
    def get_students():

        try:

            students = Student.query.order_by(
                Student.student_id.desc()
            ).all()

            return {
                "students": [
                    {
                        "student_id": student.student_id,
                        "usn": student.usn,
                        "name": student.name,
                        "email": student.email,
                        "status": student.status,
                        "enrollment_date": (
                            student.enrollment_date.isoformat()
                            if student.enrollment_date
                            else None
                        )
                    }
                    for student in students
                ]
            }

        except Exception as error:

            print("GET STUDENTS ERROR:", error)

            return {
                "success": False,
                "message": str(error)
            }, 500

    # =====================================================
    # ENROLL STUDENT
    # =====================================================

    @app.route("/api/students/enroll", methods=["POST"])
    def enroll_student():

        temp_files = []

        try:

            # -------------------------------------------------
            # GET FORM DATA
            # -------------------------------------------------

            usn = request.form.get(
                "usn",
                ""
            ).strip()

            name = request.form.get(
                "name",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip() or None

            # -------------------------------------------------
            # VALIDATION
            # -------------------------------------------------

            if not usn:
                return {
                    "success": False,
                    "message": "USN is required."
                }, 400

            if not name:
                return {
                    "success": False,
                    "message": "Student name is required."
                }, 400

            # -------------------------------------------------
            # DUPLICATE USN
            # -------------------------------------------------

            existing_student = Student.query.filter_by(
                usn=usn
            ).first()

            if existing_student:

                return {
                    "success": False,
                    "message": (
                        f"Student with USN {usn} already exists."
                    )
                }, 409

            # -------------------------------------------------
            # GET PHOTOS
            # -------------------------------------------------

            uploaded_files = request.files.getlist(
                "photos"
            )

            if not uploaded_files:

                return {
                    "success": False,
                    "message": (
                        "At least one face photo is required."
                    )
                }, 400

            uploaded_files = uploaded_files[:5]

            # -------------------------------------------------
            # SAVE TEMPORARY PHOTOS
            # -------------------------------------------------

            allowed_extensions = (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            )

            for uploaded_file in uploaded_files:

                if (
                    not uploaded_file
                    or not uploaded_file.filename
                ):
                    continue

                filename = uploaded_file.filename.lower()

                if not filename.endswith(
                    allowed_extensions
                ):
                    continue

                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=os.path.splitext(filename)[1]
                )

                uploaded_file.save(
                    temp_file.name
                )

                temp_file.close()

                temp_files.append(
                    temp_file.name
                )

            # -------------------------------------------------
            # MINIMUM 3 PHOTOS
            # -------------------------------------------------

            if len(temp_files) < 3:

                return {
                    "success": False,
                    "message": (
                        "At least 3 valid face photos "
                        "are required."
                    )
                }, 400

            # -------------------------------------------------
            # FACE EMBEDDING
            # -------------------------------------------------

            print()
            print("=" * 60)
            print("FACE ENROLLMENT")
            print("=" * 60)
            print(f"USN: {usn}")
            print(f"Name: {name}")
            print(
                f"Photos received: {len(temp_files)}"
            )
            print()

            embedding_bytes, processed_count = (
                generate_student_embedding(
                    temp_files
                )
            )

            if processed_count < 1:

                return {
                    "success": False,
                    "message": (
                        "No valid face embeddings "
                        "could be generated."
                    )
                }, 400

            # -------------------------------------------------
            # CREATE STUDENT
            # -------------------------------------------------

            student = Student(
                usn=usn,
                name=name,
                email=email,
                face_embedding=embedding_bytes,
                status="ACTIVE"
            )

            db.session.add(student)

            db.session.commit()

            # -------------------------------------------------
            # SUCCESS LOG
            # -------------------------------------------------

            print()
            print("Enrollment successful!")
            print(
                f"Student ID: {student.student_id}"
            )
            print(
                f"USN: {student.usn}"
            )
            print(
                f"Name: {student.name}"
            )
            print(
                f"Photos processed: {processed_count}"
            )
            print(
                "Embedding dimensions: 512"
            )
            print(
                "Saved to MySQL: YES"
            )
            print("=" * 60)
            print()

            # -------------------------------------------------
            # RESPONSE
            # -------------------------------------------------

            return {
                "success": True,
                "message": (
                    "Student enrolled successfully."
                ),
                "student": {
                    "student_id":
                        student.student_id,

                    "usn":
                        student.usn,

                    "name":
                        student.name,

                    "email":
                        student.email,

                    "status":
                        student.status,

                    "enrollment_date": (
                        student.enrollment_date.isoformat()
                        if student.enrollment_date
                        else None
                    )
                },
                "embedding": {
                    "dimensions": 512,
                    "photos_processed":
                        processed_count
                }
            }, 201

        except Exception as error:

            db.session.rollback()

            print()
            print("ENROLLMENT ERROR:")
            print(error)
            print()

            return {
                "success": False,
                "message": str(error)
            }, 500

        finally:

            # -------------------------------------------------
            # DELETE TEMP FILES
            # -------------------------------------------------

            for file_path in temp_files:

                try:

                    if os.path.exists(
                        file_path
                    ):
                        os.remove(
                            file_path
                        )

                except Exception as cleanup_error:

                    print(
                        "Temporary file cleanup failed:",
                        cleanup_error
                    )

    # =====================================================
    # START ATTENDANCE SESSION
    # =====================================================

    @app.route(
        "/api/sessions/start",
        methods=["POST"]
    )
    def start_session():

        try:

            data = request.get_json() or {}

            classroom_id = data.get(
                "classroom_id"
            )

            period_number = data.get(
                "period_number"
            )

            # -------------------------------------------------
            # VALIDATION
            # -------------------------------------------------

            if not classroom_id:

                return {
                    "success": False,
                    "message": (
                        "Classroom ID is required."
                    )
                }, 400

            if not period_number:

                return {
                    "success": False,
                    "message": (
                        "Period number is required."
                    )
                }, 400

            # -------------------------------------------------
            # CLASSROOM
            # -------------------------------------------------

            classroom = Classroom.query.filter_by(
                classroom_id=classroom_id
            ).first()

            if not classroom:

                return {
                    "success": False,
                    "message": (
                        "Classroom not found."
                    )
                }, 404

            today = date.today()

            # -------------------------------------------------
            # CHECK EXISTING SESSION
            # -------------------------------------------------

            existing = Session.query.filter_by(
                classroom_id=classroom_id,
                period_number=period_number,
                date=today
            ).first()

            if existing:

                existing.status = "ACTIVE"

                db.session.commit()

                return {
                    "success": True,
                    "message": (
                        "Existing session activated."
                    ),
                    "session": {
                        "session_id":
                            existing.session_id,

                        "classroom_id":
                            existing.classroom_id,

                        "period_number":
                            existing.period_number,

                        "date":
                            str(existing.date),

                        "status":
                            existing.status
                    }
                }

            # -------------------------------------------------
            # CREATE NEW SESSION
            # -------------------------------------------------

            new_session = Session(
                classroom_id=classroom_id,
                period_number=period_number,
                date=today,
                start_time=datetime.now().time(),
                end_time=time(
                    23,
                    59,
                    59
                ),
                status="ACTIVE"
            )

            db.session.add(
                new_session
            )

            db.session.commit()

            return {
                "success": True,
                "message": (
                    "Attendance session started."
                ),
                "session": {
                    "session_id":
                        new_session.session_id,

                    "classroom_id":
                        new_session.classroom_id,

                    "period_number":
                        new_session.period_number,

                    "date":
                        str(new_session.date),

                    "status":
                        new_session.status
                }
            }, 201

        except Exception as error:

            db.session.rollback()

            print(
                "SESSION START ERROR:",
                error
            )

            return {
                "success": False,
                "message": str(error)
            }, 500

    # =====================================================
    # STOP ATTENDANCE SESSION
    # =====================================================

    @app.route(
        "/api/sessions/<int:session_id>/stop",
        methods=["POST"]
    )
    def stop_session(session_id):

        try:

            session = Session.query.filter_by(
                session_id=session_id
            ).first()

            if not session:

                return {
                    "success": False,
                    "message": (
                        "Session not found."
                    )
                }, 404

            session.status = "COMPLETED"

            session.end_time = (
                datetime.now().time()
            )

            db.session.commit()

            return {
                "success": True,
                "message": "Session stopped.",
                "session_id":
                    session.session_id
            }

        except Exception as error:

            db.session.rollback()

            print(
                "SESSION STOP ERROR:",
                error
            )

            return {
                "success": False,
                "message": str(error)
            }, 500

    # =====================================================
    # RECOGNIZE FACE + MARK ATTENDANCE
    # =====================================================

    @app.route(
        "/api/attendance/recognize",
        methods=["POST"]
    )
    def recognize_attendance():

        try:

            # -------------------------------------------------
            # SESSION ID
            # -------------------------------------------------

            session_id = request.form.get(
                "session_id"
            )

            if not session_id:

                return {
                    "success": False,
                    "message": (
                        "Session ID is required."
                    )
                }, 400

            # -------------------------------------------------
            # ACTIVE SESSION
            # -------------------------------------------------

            session = Session.query.filter_by(
                session_id=session_id,
                status="ACTIVE"
            ).first()

            if not session:

                return {
                    "success": False,
                    "message": (
                        "Active session not found."
                    )
                }, 404

            # -------------------------------------------------
            # IMAGE
            # -------------------------------------------------

            image = request.files.get(
                "image"
            )

            if not image:

                return {
                    "success": False,
                    "message": (
                        "Camera image is required."
                    )
                }, 400

            # -------------------------------------------------
            # TEMP IMAGE
            # -------------------------------------------------

            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg"
            )

            image.save(
                temp_file.name
            )

            temp_file.close()

            try:

                # -------------------------------------------------
                # GET ACTIVE STUDENTS
                # -------------------------------------------------

                students = Student.query.filter_by(
                    status="ACTIVE"
                ).all()

                # -------------------------------------------------
                # FACE RECOGNITION
                # -------------------------------------------------

                result = recognize_face(
                    temp_file.name,
                    students
                )

            finally:

                if os.path.exists(
                    temp_file.name
                ):
                    os.remove(
                        temp_file.name
                    )

            # -------------------------------------------------
            # UNKNOWN FACE
            # -------------------------------------------------

            if not result["matched"]:

                return {
                    "success": True,
                    "matched": False,
                    "message": "Unknown face.",
                    "distance":
                        result["distance"]
                }

            # -------------------------------------------------
            # MATCH FOUND
            # -------------------------------------------------

            student = result["student"]

            distance = result["distance"]

            # -------------------------------------------------
            # DUPLICATE CHECK
            # -------------------------------------------------

            existing_attendance = (
                Attendance.query.filter_by(
                    student_id=
                        student.student_id,

                    session_id=
                        session.session_id
                ).first()
            )

            if existing_attendance:

                return {
                    "success": True,
                    "matched": True,
                    "already_marked": True,

                    "student": {
                        "student_id":
                            student.student_id,

                        "usn":
                            student.usn,

                        "name":
                            student.name
                    },

                    "distance":
                        distance
                }

            # -------------------------------------------------
            # MARK ATTENDANCE
            # -------------------------------------------------

            attendance = Attendance(

                student_id=
                    student.student_id,

                session_id=
                    session.session_id,

                detected_at=
                    datetime.utcnow(),

                confidence=max(
                    0,
                    min(
                        100,
                        (1 - distance) * 100
                    )
                ),

                embedding_distance=
                    distance,

                liveness_score=None,

                status="PRESENT",

                marked_by="SYSTEM"
            )

            db.session.add(
                attendance
            )

            db.session.commit()

            print(
                f"ATTENDANCE MARKED: "
                f"{student.name} "
                f"({student.usn}) "
                f"distance={distance:.4f}"
            )

            # -------------------------------------------------
            # RESPONSE
            # -------------------------------------------------

            return {

                "success": True,

                "matched": True,

                "already_marked": False,

                "student": {

                    "student_id":
                        student.student_id,

                    "usn":
                        student.usn,

                    "name":
                        student.name
                },

                "attendance": {

                    "attendance_id":
                        attendance.attendance_id,

                    "confidence":
                        attendance.confidence,

                    "distance":
                        attendance.embedding_distance,

                    "detected_at":
                        attendance.detected_at.isoformat()
                }
            }

        except Exception as error:

            db.session.rollback()

            print(
                "RECOGNITION ERROR:",
                error
            )

            return {
                "success": False,
                "message": str(error)
            }, 500

    # =====================================================
    # GET ATTENDANCE RECORDS
    # =====================================================

    @app.route(
        "/api/attendance",
        methods=["GET"]
    )
    def get_attendance():

        try:

            records = Attendance.query.order_by(
                Attendance.detected_at.desc()
            ).all()

            return {

                "attendance": [

                    {

                        "attendance_id":
                            record.attendance_id,

                        "student_id":
                            record.student_id,

                        "student_name":
                            record.student.name,

                        "usn":
                            record.student.usn,

                        "session_id":
                            record.session_id,

                        "classroom": (
                            record.session.classroom.classroom_name
                            if record.session.classroom
                            else None
                        ),

                        "period_number":
                            record.session.period_number,

                        "date":
                            str(record.session.date),

                        "time":
                            record.detected_at.strftime(
                                "%I:%M:%S %p"
                            ),

                        "confidence":
                            record.confidence,

                        "distance":
                            record.embedding_distance,

                        "status":
                            record.status
                    }

                    for record in records
                ]
            }

        except Exception as error:

            print(
                "GET ATTENDANCE ERROR:",
                error
            )

            return {
                "success": False,
                "message": str(error)
            }, 500

    # =====================================================
    # GET CLASSROOMS
    # =====================================================

    @app.route(
        "/api/classrooms",
        methods=["GET"]
    )
    def get_classrooms():

        try:

            classrooms = Classroom.query.order_by(
                Classroom.classroom_id.asc()
            ).all()

            return {
                "classrooms": [
                    {
                        "classroom_id":
                            classroom.classroom_id,

                        "classroom_name":
                            classroom.classroom_name,

                        "camera_source":
                            classroom.camera_source,

                        "capacity":
                            classroom.capacity,

                        "status":
                            classroom.status
                    }

                    for classroom in classrooms
                ]
            }

        except Exception as error:

            print(
                "GET CLASSROOMS ERROR:",
                error
            )

            return {
                "success": False,
                "message": str(error)
            }, 500

    # =====================================================
    # GET SESSIONS
    # =====================================================

    @app.route(
        "/api/sessions",
        methods=["GET"]
    )
    def get_sessions():

        try:

            sessions = Session.query.order_by(
                Session.date.desc(),
                Session.session_id.desc()
            ).all()

            return {
                "sessions": [
                    {
                        "session_id":
                            session.session_id,

                        "classroom_id":
                            session.classroom_id,

                        "classroom_name": (
                            session.classroom.classroom_name
                            if session.classroom
                            else None
                        ),

                        "period_number":
                            session.period_number,

                        "date":
                            str(session.date),

                        "start_time":
                            session.start_time.strftime(
                                "%H:%M:%S"
                            )
                            if session.start_time
                            else None,

                        "end_time":
                            session.end_time.strftime(
                                "%H:%M:%S"
                            )
                            if session.end_time
                            else None,

                        "status":
                            session.status
                    }

                    for session in sessions
                ]
            }

        except Exception as error:

            print(
                "GET SESSIONS ERROR:",
                error
            )

            return {
                "success": False,
                "message": str(error)
            }, 500

    # =====================================================
    # GET DASHBOARD SUMMARY
    # =====================================================

    @app.route(
        "/api/dashboard",
        methods=["GET"]
    )
    def dashboard():

        try:

            total_students = Student.query.filter_by(
                status="ACTIVE"
            ).count()

            today = date.today()

            today_attendance = (
                Attendance.query.join(
                    Session
                ).filter(
                    Session.date == today,
                    Attendance.status == "PRESENT"
                ).count()
            )

            active_session = Session.query.filter_by(
                status="ACTIVE"
            ).order_by(
                Session.session_id.desc()
            ).first()

            attendance_rate = 0

            if total_students > 0:

                attendance_rate = round(
                    (
                        today_attendance
                        / total_students
                    ) * 100,
                    1
                )

            return {

                "success": True,

                "total_students":
                    total_students,

                "today_attendance":
                    today_attendance,

                "attendance_rate":
                    attendance_rate,

                "active_session": (
                    {
                        "session_id":
                            active_session.session_id,

                        "classroom_id":
                            active_session.classroom_id,

                        "classroom_name": (
                            active_session.classroom.classroom_name
                            if active_session.classroom
                            else None
                        ),

                        "period_number":
                            active_session.period_number,

                        "status":
                            active_session.status
                    }
                    if active_session
                    else None
                )
            }

        except Exception as error:

            print(
                "DASHBOARD ERROR:",
                error
            )

            return {
                "success": False,
                "message": str(error)
            }, 500

    return app


# =========================================================
# CREATE APP
# =========================================================

app = create_app()


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )