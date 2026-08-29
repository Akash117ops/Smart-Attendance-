import cv2
import numpy as np
import mysql.connector
import pickle
from deepface import DeepFace

# =============================
# SETTINGS
# =============================

MATCH_THRESHOLD = 0.40
PROCESS_EVEMATCH_THRESHOLD = 0.40
PROCESS_EVERY_N_FRAMES = 10
SESSION_ID = 1

# Minimum number of REAL faces required
MIN_REQUIRED_FACES = 3RY_N_FRAMES = 10
SESSION_ID = 1

# =============================
# MYSQL CONNECTION
# =============================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Akash117",
    database="smart_attendance"
)

cursor = db.cursor()

# =============================
# LOAD ENROLLED STUDENTS
# =============================

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

# =============================
# GENERATE FACE EMBEDDING
# =============================

def get_embedding(face_crop):

    result = DeepFace.represent(
        img_path=face_crop,
        model_name="Facenet512",
        detector_backend="skip",
        enforce_detection=False
    )

    return np.array(
        result[0]["embedding"],
        dtype=np.float32
    )


# =============================
# RECOGNITION
# =============================

def recognize(embedding):

    best_student = None
    best_distance = float("inf")

    for student in students:

        stored = student["embedding"]

        similarity = np.dot(
            embedding,
            stored
        ) / (
            np.linalg.norm(embedding)
            * np.linalg.norm(stored)
        )

        distance = 1 - similarity

        if distance < best_distance:

            best_distance = distance
            best_student = student

    if (
        best_student is not None
        and best_distance < MATCH_THRESHOLD
    ):

        return best_student, best_distance

    return None, best_distance


# =============================
# MARK ATTENDANCE
# =============================

def mark_attendance(student, distance):

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
        "Anti-spoofing + FaceNet512"
    ))

    db.commit()

    return True


# =============================
# START CAMERA
# =============================

cap = cv2.VideoCapture(0)

frame_count = 0

print()
print("========================================")
print("LIVE ATTENDANCE STARTED")
print("========================================")
print("Anti-spoofing: ENABLED")
print("FaceNet512 recognition: ENABLED")
print("Multiple face detection: ENABLED")
print("Press Q to quit.")
print()


# =============================
# MAIN LOOP
# =============================

while True:

    ret, frame = cap.read()

    if not ret:
        print("Camera error.")
        break

    display_frame = frame.copy()

    try:

        # ==================================
        # DETECT ALL FACES + ANTI-SPOOF
        # ==================================

        results = DeepFace.extract_faces(
            img_path=frame,
            detector_backend="mtcnn",
            enforce_detection=False,
            align=True,
            anti_spoofing=True
        )

        face_count = len(results)

        # ==================================
        # PROCESS EVERY DETECTED FACE
        # ==================================

      # ==================================
# PROCESS EVERY DETECTED FACE
# ==================================

real_faces = []

for face_data in results:

    area = face_data["facial_area"]

    x = max(0, area["x"])
    y = max(0, area["y"])

    x2 = min(
        frame.shape[1],
        x + area["w"]
    )

    y2 = min(
        frame.shape[0],
        y + area["h"]
    )

    if x2 <= x or y2 <= y:
        continue

    # ==================================
    # ANTI-SPOOF RESULT
    # ==================================

    is_real = face_data.get(
        "is_real",
        False
    )

    spoof_score = face_data.get(
        "antispoof_score",
        0.0
    )

    # ==================================
    # SPOOF FACE
    # ==================================

    if not is_real:

        color = (0, 0, 255)

        label = (
            f"SPOOF | {spoof_score:.3f}"
        )

        cv2.rectangle(
            display_frame,
            (x, y),
            (x2, y2),
            color,
            3
        )

        cv2.putText(
            display_frame,
            label,
            (x, max(30, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            color,
            2
        )

        continue

    # ==================================
    # REAL FACE
    # ==================================

    color = (0, 255, 0)

    label = (
        f"REAL | {spoof_score:.3f}"
    )

    cv2.rectangle(
        display_frame,
        (x, y),
        (x2, y2),
        color,
        3
    )

    cv2.putText(
        display_frame,
        label,
        (x, max(30, y - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2
    )

    # Save REAL face for later recognition
    real_faces.append({
        "x": x,
        "y": y,
        "x2": x2,
        "y2": y2
    })


# ==================================
# MINIMUM FACE REQUIREMENT
# ==================================

real_face_count = len(real_faces)

if real_face_count < MIN_REQUIRED_FACES:

    cv2.putText(
        display_frame,
        f"WAITING: {real_face_count}/{MIN_REQUIRED_FACES} REAL FACES",
        (20, 145),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 165, 255),
        2
    )

else:

    cv2.putText(
        display_frame,
        f"ATTENDANCE ACTIVE: {real_face_count} REAL FACES",
        (20, 145),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    # ==================================
    # RECOGNIZE ALL REAL FACES
    # ==================================

    if frame_count % PROCESS_EVERY_N_FRAMES == 0:

        for face in real_faces:

            x = face["x"]
            y = face["y"]
            x2 = face["x2"]
            y2 = face["y2"]

            try:

                face_crop = frame[
                    y:y2,
                    x:x2
                ]

                if face_crop.size == 0:
                    continue

                embedding = get_embedding(
                    face_crop
                )

                student, distance = recognize(
                    embedding
                )

                # ==================================
                # RECOGNIZED STUDENT
                # ==================================

                if student:

                    marked = mark_attendance(
                        student,
                        distance
                    )

                    name = student["name"]
                    usn = student["usn"]

                    student_label = (
                        f"{name} | D:{distance:.3f}"
                    )

                    cv2.putText(
                        display_frame,
                        student_label,
                        (x, y2 + 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 255, 0),
                        2
                    )

                    if marked:

                        print(
                            f"ATTENDANCE MARKED: "
                            f"{name} ({usn})"
                        )

                    else:

                        print(
                            f"Already marked: "
                            f"{name} ({usn})"
                        )

                # ==================================
                # UNKNOWN REAL PERSON
                # ==================================

                else:

                    cv2.putText(
                        display_frame,
                        f"UNKNOWN | D:{distance:.3f}",
                        (x, y2 + 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 165, 255),
                        2
                    )

            except Exception as e:

                print(
                    "Recognition error:",
                    e
                )

                cv2.putText(
                    display_frame,
                    "Recognition error",
                    (x, y2 + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )

    # ==================================
    # DISPLAY INFORMATION
    # ==================================

    cv2.putText(
        display_frame,
        f"Faces detected: {face_count}",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.putText(
        display_frame,
        f"Students enrolled: {len(students)}",
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.putText(
        display_frame,
        "Anti-Spoofing: ON",
        (20, 105),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.imshow(
        "Smart Attendance - Live Attendance",
        display_frame
    )

    frame_count += 1

    # ==================================
    # QUIT
    # ==================================

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# =============================
# CLEANUP
# =============================

cap.release()

cv2.destroyAllWindows()

cursor.close()

db.close()

print()
print("========================================")
print("LIVE ATTENDANCE STOPPED")
print("========================================")