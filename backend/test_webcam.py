import cv2
from app import app
from models import Student
from recognition_service import recognize_face


with app.app_context():

    students = Student.query.filter_by(
        status="ACTIVE"
    ).all()

    print(f"Loaded {len(students)} enrolled students.")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        exit()

    print("Webcam started.")
    print("Press Q to quit.")

    while True:

        ret, frame = cap.read()

        if not ret:
            print("Failed to read webcam frame.")
            break

        cv2.imshow(
            "Smart Attendance - Webcam Test",
            frame
        )

        # Test recognition when SPACE is pressed
        key = cv2.waitKey(1) & 0xFF

        if key == ord(" "):

            print("\nRecognizing...")

            try:

                result = recognize_face(
                    frame,
                    students
                )

                if result["matched"]:

                    student = result["student"]

                    print(
                        f"MATCH: "
                        f"{student.name} "
                        f"({student.usn}) "
                        f"distance="
                        f"{result['distance']:.4f}"
                    )

                else:

                    print(
                        "UNKNOWN FACE | "
                        f"best distance="
                        f"{result['distance']}"
                    )

            except Exception as error:

                print(
                    "Recognition error:",
                    error
                )

        elif key == ord("q"):

            break

    cap.release()
    cv2.destroyAllWindows()