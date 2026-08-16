import pickle
import numpy as np
from deepface import DeepFace


MODEL_NAME = "Facenet512"
DETECTOR = "mtcnn"

# Start with the threshold that worked well in your testing.
DISTANCE_THRESHOLD = 0.40


def cosine_distance(a, b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)

    denominator = (
        np.linalg.norm(a) *
        np.linalg.norm(b)
    )

    if denominator == 0:
        return 1.0

    similarity = np.dot(a, b) / denominator

    return float(1.0 - similarity)


def generate_embedding(image):
    """
    Generate a 512-dimensional FaceNet512
    embedding from an image.
    """

    result = DeepFace.represent(
        img_path=image,
        model_name=MODEL_NAME,
        detector_backend=DETECTOR,
        enforce_detection=True
    )

    embedding = np.asarray(
        result[0]["embedding"],
        dtype=np.float32
    )

    if len(embedding) != 512:
        raise ValueError(
            f"Expected 512 dimensions, got {len(embedding)}"
        )

    # Normalize
    norm = np.linalg.norm(embedding)

    if norm == 0:
        raise ValueError("Invalid zero embedding.")

    embedding = embedding / norm

    return embedding


def recognize_face(image, students):
    """
    Compare a detected face against all enrolled students.

    Returns:
        {
            "matched": True/False,
            "student": Student object or None,
            "distance": float or None
        }
    """

    query_embedding = generate_embedding(image)

    best_student = None
    best_distance = float("inf")

    for student in students:

        if not student.face_embedding:
            continue

        try:
            stored_embedding = pickle.loads(
                student.face_embedding
            )

            stored_embedding = np.asarray(
                stored_embedding,
                dtype=np.float32
            )

            distance = cosine_distance(
                query_embedding,
                stored_embedding
            )

            if distance < best_distance:
                best_distance = distance
                best_student = student

        except Exception as error:
            print(
                f"Skipping {student.usn}: {error}"
            )

    if (
        best_student is not None
        and best_distance <= DISTANCE_THRESHOLD
    ):
        return {
            "matched": True,
            "student": best_student,
            "distance": best_distance
        }

    return {
        "matched": False,
        "student": None,
        "distance": (
            best_distance
            if best_distance != float("inf")
            else None
        )
    }