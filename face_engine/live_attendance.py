import cv2
import numpy as np
import mysql.connector
import pickle
from mtcnn import MTCNN
from deepface import DeepFace

MATCH_THRESHOLD = 0.40
PROCESS_EVERY_N_FRAMES = 10
LIVENESS_WINDOW = 20
MOVEMENT_THRESHOLD = 20

SESSION_ID = 1

# -----------------------------
# FACE DETECTOR
# -----------------------------
detector = MTCNN()

# -----------------------------
# MYSQL CONNECTION
# -----------------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Akash117",
    database="smart_attendance"
)

cursor = db.cursor()

# -----------------------------
# LOAD ENROLLED STUDENTS
# -----------------------------
print("Loading enrolled students from MySQL...")

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


# -----------------------------
# GENERATE EMBEDDING
# -----------------------------
def get_embedding(frame):

    result = DeepFace.represent(
        img_path=frame,
        model_name="Facenet512",
        detector_backend="mtcnn",
        enforce_detection=True
    )

    return np.array(result[0]["embedding"])


# -----------------------------
# RECOGNITION
# -----------------------------
def recognize(embedding):

    best_student = None
    best_distance = float("inf")

    for student in students:

        stored = student["embedding"]

        similarity = np.dot(embedding, stored) / (
            np.linalg.norm(embedding)
            * np.linalg.norm(stored)
        )

        distance = 1 - similarity

        if distance < best_distance:
            best_distance = distance
            best_student = student

    if best_student and best_distance < MATCH_THRESHOLD:
        return best_student, best_distance

    return None, best_distance


# -----------------------------
# MARK ATTENDANCE
# -----------------------------
def mark_attendance(student, distance):

    # Check duplicate attendance
    cursor.execute("""
        SELECT attendance_id
        FROM attendance
        WHERE student_id = %s
        AND session_id = %s
    """, (
        student["student_id"],
        SESSION_ID
    ))

    existing = cursor.fetchone()

    if existing:
        return False

    # Insert attendance
    cursor.execute("""
        INSERT INTO attendance
        (
            student_id,
            session_id,
            detected_at,
            confidence,
            liveness_score,
            embedding_distance,
            status,
            marked_by,
            notes
        )
        VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s, %s)
    """, (
        student["student_id"],
        SESSION_ID,
        1 - distance,
        1.0,
        distance,
        "Present",
        "AI",
        "Live face recognition"
    ))

    db.commit()

    return True


# -----------------------------
# START WEBCAM
# -----------------------------
cap = cv2.VideoCapture(0)

frame_count = 0
positions = []

status = "Scanning..."
distance = None

print()
print("Live attendance started.")
print("Move your head slightly.")
print("Press Q to quit.")
print()


# -----------------------------
# MAIN LOOP
# -----------------------------
while True:

    ret, frame = cap.read()

    if not ret:
        break

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    faces = detector.detect_faces(rgb)

    liveness = "NO FACE"

    if faces:

        # Select largest face
        face = max(
            faces,
            key=lambda f: f["box"][2] * f["box"][3]
        )

        x, y, w, h = face["box"]

        # Prevent negative coordinates
        x = max(0, x)
        y = max(0, y)

        # Face centre
        center_x = x + w // 2
        center_y = y + h // 2

        positions.append(
            (center_x, center_y)
        )

        if len(positions) > LIVENESS_WINDOW:
            positions.pop(0)

        # -----------------------------
        # LIVENESS
        # -----------------------------
        if len(positions) >= LIVENESS_WINDOW:

            movement = np.ptp(
                np.array(positions),
                axis=0
            )

            total_movement = (
                movement[0] + movement[1]
            )

            if total_movement > MOVEMENT_THRESHOLD:
                liveness = "LIVE"
            else:
                liveness = "MOVE HEAD"

        # Draw face box
        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        # -----------------------------
        # RECOGNITION
        # -----------------------------
        if (
            frame_count % PROCESS_EVERY_N_FRAMES == 0
            and liveness == "LIVE"
        ):

            try:

                face_crop = frame[
                    y:y + h,
                    x:x + w
                ]

                embedding = get_embedding(
                    face_crop
                )

                student, distance = recognize(
                    embedding
                )

                if student:

                    # Mark attendance
                    marked = mark_attendance(
                        student,
                        distance
                    )

                    status = (
                        f"{student['name']} "
                        f"({student['usn']})"
                    )

                    if marked:

                        print(
                            f"ATTENDANCE MARKED: "
                            f"{student['name']} "
                            f"({student['usn']})"
                        )

                    else:

                        print(
                            f"Already marked: "
                            f"{student['name']} "
                            f"({student['usn']})"
                        )

                else:

                    status = "UNKNOWN"

            except Exception as e:

                status = "Recognition failed"
                print("Recognition error:", e)

    else:

        status = "Scanning..."
        distance = None
        positions.clear()

    frame_count += 1

    # -----------------------------
    # DISPLAY
    # -----------------------------
    cv2.putText(
        frame,
        f"Liveness: {liveness}",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        status,
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    if distance is not None:

        cv2.putText(
            frame,
            f"Distance: {distance:.3f}",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

    cv2.imshow(
        "Smart Attendance - Live Attendance",
        frame
    )

    # Q = quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# -----------------------------
# CLEANUP
# -----------------------------
cap.release()
cv2.destroyAllWindows()

cursor.close()
db.close()

print()
print("Live attendance stopped.")