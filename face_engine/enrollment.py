from deepface import DeepFace
import numpy as np
import os
import mysql.connector
from datetime import datetime
import pickle


# ==============================
# STUDENT DETAILS
# ==============================

STUDENT_USN = "1AM24IS001"
STUDENT_NAME = "Akash"
STUDENT_EMAIL = "akash@example.com"

IMAGE_FOLDER = "dataset/test"


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
# GENERATE FACE EMBEDDING
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
# ENROLL STUDENT
# ==============================

def enroll_student():

    embeddings = []

    for filename in os.listdir(IMAGE_FOLDER):

        if filename.lower().endswith((".jpg", ".jpeg", ".png")):

            image_path = os.path.join(IMAGE_FOLDER, filename)

            print(f"Processing: {filename}")

            embedding = generate_embedding(image_path)

            embeddings.append(embedding)

            print(f"Embedding generated: {len(embedding)} dimensions")


    if len(embeddings) == 0:

        print("No images found.")

        return


    # Create representative embedding
    average_embedding = np.mean(embeddings, axis=0)


    # Convert numpy array into binary data
    embedding_blob = pickle.dumps(average_embedding)


    # Insert student into database
    query = """
        INSERT INTO students
        (usn, name, email, enrollment_date, status, face_embedding)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (
        STUDENT_USN,
        STUDENT_NAME,
        STUDENT_EMAIL,
        datetime.now(),
        "active",
        embedding_blob
    )


    cursor.execute(query, values)

    db.commit()


    print()
    print("================================")
    print("STUDENT ENROLLMENT SUCCESSFUL")
    print("================================")
    print("USN:", STUDENT_USN)
    print("Name:", STUDENT_NAME)
    print("Photos processed:", len(embeddings))
    print("Embedding dimensions:", len(average_embedding))
    print("Saved to MySQL: YES")


# ==============================
# RUN
# ==============================

if __name__ == "__main__":

    try:

        enroll_student()

    except Exception as e:

        print()
        print("ERROR:", e)

    finally:

        cursor.close()
        db.close()