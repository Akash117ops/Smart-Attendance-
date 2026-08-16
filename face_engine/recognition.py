from deepface import DeepFace
import numpy as np
import mysql.connector
import pickle
from sklearn.metrics.pairwise import cosine_distances


# ==============================
# SETTINGS
# ==============================

TEST_IMAGE = "dataset/test/akash1.jpg"

# Lower distance = better match
MATCH_THRESHOLD = 0.40


# ==============================
# MYSQL CONNECTION
# ==============================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Akash117",
    database="smart_attendance"
)

cursor = db.cursor()


# ==============================
# GENERATE EMBEDDING
# ==============================

def generate_embedding(image_path):

    result = DeepFace.represent(
        img_path=image_path,
        model_name="Facenet512",
        detector_backend="mtcnn",
        enforce_detection=True
    )

    return np.array(result[0]["embedding"])


# ==============================
# LOAD STUDENTS
# ==============================

def load_students():

    cursor.execute("""
        SELECT student_id, usn, name, face_embedding
        FROM students
        WHERE status = 'active'
          AND face_embedding IS NOT NULL
    """)

    rows = cursor.fetchall()

    students = []

    for row in rows:

        student_id = row[0]
        usn = row[1]
        name = row[2]
        embedding_blob = row[3]

        embedding = pickle.loads(embedding_blob)

        students.append({
            "student_id": student_id,
            "usn": usn,
            "name": name,
            "embedding": embedding
        })

    return students


# ==============================
# FIND BEST MATCH
# ==============================

def recognize_face(test_embedding, students):

    best_student = None
    best_distance = float("inf")

    for student in students:

        stored_embedding = student["embedding"]

        distance = cosine_distances(
            [test_embedding],
            [stored_embedding]
        )[0][0]

        print(
            f"{student['name']} "
            f"({student['usn']}) → "
            f"distance: {distance:.3f}"
        )

        if distance < best_distance:

            best_distance = distance
            best_student = student

    if best_student is None:
        return None, best_distance

    if best_distance < MATCH_THRESHOLD:

        return best_student, best_distance

    return None, best_distance


# ==============================
# MAIN
# ==============================

def main():

    print("Generating embedding for test image...")

    test_embedding = generate_embedding(TEST_IMAGE)

    print(
        f"Test embedding dimensions: "
        f"{len(test_embedding)}"
    )

    print("\nLoading enrolled students from MySQL...")

    students = load_students()

    print(
        f"Students loaded: {len(students)}"
    )

    print("\nComparing embeddings...\n")

    student, distance = recognize_face(
        test_embedding,
        students
    )

    print("\n==============================")

    if student:

        print("RESULT: MATCH")
        print("Student:", student["name"])
        print("USN:", student["usn"])
        print(f"Cosine Distance: {distance:.3f}")

    else:

        print("RESULT: UNKNOWN")
        print(f"Best Distance: {distance:.3f}")

    print("==============================")


if __name__ == "__main__":

    try:
        main()

    except Exception as e:

        print("\nERROR:", e)

    finally:

        cursor.close()
        db.close()