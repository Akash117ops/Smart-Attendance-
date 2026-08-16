from flask import Flask
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


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return {
            "project": "AI-Based Smart Attendance Management System",
            "status": "Backend and database are connected",
            "version": "1.0"
        }

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)