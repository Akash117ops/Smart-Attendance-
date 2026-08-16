from app import app
from models import Student
from recognition_service import recognize_face


IMAGE_PATH = r"C:\Users\fanto\OneDrive\Desktop\mahesh.jpg"


with app.app_context():

    students = Student.query.filter_by(
        status="ACTIVE"
    ).all()

    print()
    print("=" * 60)
    print("FACE RECOGNITION TEST")
    print("=" * 60)

    print(f"Students loaded: {len(students)}")

    result = recognize_face(
        IMAGE_PATH,
        students
    )

    print()

    if result["matched"]:

        student = result["student"]

        print("MATCH FOUND")
        print(f"USN: {student.usn}")
        print(f"Name: {student.name}")
        print(
            f"Cosine distance: "
            f"{result['distance']:.4f}"
        )

    else:

        print("NO MATCH")
        print(
            f"Best distance: "
            f"{result['distance']}"
        )

    print("=" * 60)