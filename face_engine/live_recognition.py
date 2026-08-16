import cv2
import numpy as np
import mysql.connector
import pickle
from deepface import DeepFace


MATCH_THRESHOLD = 0.40
PROCESS_EVERY_N_FRAMES = 10

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Akash117",
    database="smart_attendance"
)

cursor = db.cursor()

# Load enrolled students ONCE
cursor.execute("""
    SELECT student_id, usn, name, face_embedding
    FROM students
    WHERE status = 'active'
    AND face_embedding IS NOT NULL
""")

students = []

for row in cursor.fetchall():
    students.append({
        "student_id": row[0],
        "usn": row[1],
        "name": row[2],
        "embedding": pickle.loads(row[3])
    })

print(f"Students loaded: {len(students)}")


def get_embedding(frame):
    result = DeepFace.represent(
        img_path=frame,
        model_name="Facenet512",
        detector_backend="mtcnn",
        enforce_detection=True
    )

    return np.array(result[0]["embedding"])


def recognize(embedding):

    best_student = None
    best_distance = float("inf")

    for student in students:

        stored = student["embedding"]

        dot = np.dot(embedding, stored)
        norm1 = np.linalg.norm(embedding)
        norm2 = np.linalg.norm(stored)

        similarity = dot / (norm1 * norm2)
        distance = 1 - similarity

        if distance < best_distance:
            best_distance = distance
            best_student = student

    if best_student and best_distance < MATCH_THRESHOLD:
        return best_student, best_distance

    return None, best_distance


cap = cv2.VideoCapture(0)

frame_count = 0
current_name = "Scanning..."
current_distance = None

print("Live recognition started. Press Q to quit.")

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_count += 1

    # Run expensive recognition only every N frames
    if frame_count % PROCESS_EVERY_N_FRAMES == 0:

        try:

            embedding = get_embedding(frame)

            student, distance = recognize(embedding)

            if student:
                current_name = f"{student['name']} ({student['usn']})"
                current_distance = distance
            else:
                current_name = "UNKNOWN"
                current_distance = distance

        except Exception:
            current_name = "No face detected"
            current_distance = None

    # Display result
    cv2.putText(
        frame,
        current_name,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    if current_distance is not None:

        cv2.putText(
            frame,
            f"Distance: {current_distance:.3f}",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

    cv2.imshow("Smart Attendance - Live Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()

cursor.close()
db.close()