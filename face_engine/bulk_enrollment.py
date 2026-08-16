import os
import pickle
import numpy as np
import mysql.connector
from deepface import DeepFace
from dotenv import load_dotenv

load_dotenv()

DATASET = "dataset/enrollment"

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_NAME")
)
cursor = db.cursor()

for usn in os.listdir(DATASET):

    student_folder = os.path.join(DATASET, usn)

    if not os.path.isdir(student_folder):
        continue

    # --------------------------------
    # CHECK IF ALREADY ENROLLED
    # --------------------------------
    cursor.execute("""
        SELECT student_id, name
        FROM students
        WHERE usn = %s
        AND face_embedding IS NOT NULL
    """, (usn,))

    existing = cursor.fetchone()

    if existing:
        print(f"\nSKIPPING {usn} - already enrolled as {existing[1]}")
        continue

    print("\n================================")
    print("Processing:", usn)
    print("================================")

    embeddings = []

    # --------------------------------
    # PROCESS PHOTOS
    # --------------------------------
    for filename in os.listdir(student_folder):

        image_path = os.path.join(
            student_folder,
            filename
        )

        if not filename.lower().endswith(
            (".jpg", ".jpeg", ".png")
        ):
            continue

        print("Processing:", filename)

        try:

            result = DeepFace.represent(
                img_path=image_path,
                model_name="Facenet512",
                detector_backend="mtcnn",
                enforce_detection=True
            )

            embedding = np.array(
                result[0]["embedding"],
                dtype=np.float32
            )

            embeddings.append(embedding)

            print(
                "Embedding generated:",
                len(embedding)
            )

        except Exception as e:

            print(
                "SKIPPED PHOTO:",
                filename
            )

            print(
                "Reason:",
                str(e)[:200]
            )

            continue

    # --------------------------------
    # NO VALID PHOTOS
    # --------------------------------
    if not embeddings:

        print(
            "NO VALID PHOTOS FOR:",
            usn
        )

        continue

    # --------------------------------
    # AVERAGE EMBEDDINGS
    # --------------------------------
    final_embedding = np.mean(
        embeddings,
        axis=0
    )

    # --------------------------------
    # NORMALIZE
    # --------------------------------
    final_embedding = (
        final_embedding /
        np.linalg.norm(final_embedding)
    )

    embedding_blob = pickle.dumps(
        final_embedding
    )

    # --------------------------------
    # GET STUDENT NAME
    # --------------------------------
    name = input(
        f"Enter name for {usn}: "
    ).strip()

    if not name:
        print(
            "No name entered. Skipping:",
            usn
        )
        continue

    # --------------------------------
    # INSERT NEW STUDENT
    # --------------------------------
    cursor.execute("""
        INSERT INTO students
        (
            usn,
            name,
            enrollment_date,
            status,
            face_embedding
        )
        VALUES
        (
            %s,
            %s,
            NOW(),
            'active',
            %s
        )
    """, (
        usn,
        name,
        embedding_blob
    ))

    db.commit()

    print("\n--------------------------------")
    print("NEW STUDENT ENROLLED")
    print("USN:", usn)
    print("Name:", name)
    print(
        "Valid photos:",
        len(embeddings)
    )
    print(
        "Final embedding dimensions:",
        len(final_embedding)
    )
    print("Saved to MySQL: YES")
    print("--------------------------------")


cursor.close()
db.close()

print("\n================================")
print("BULK ENROLLMENT COMPLETE")
print("================================")