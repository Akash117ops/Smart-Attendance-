import pickle
import numpy as np
from deepface import DeepFace


MODEL_NAME = "Facenet512"

# Used when generating an embedding from an already
# detected face crop.
EMBEDDING_DETECTOR = "skip"

# Face recognition threshold
DISTANCE_THRESHOLD = 0.40

# Minimum number of faces required in a classroom frame
MIN_FACES_REQUIRED = 3


# =========================================================
# COSINE DISTANCE
# =========================================================

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


# =========================================================
# GENERATE EMBEDDING FROM FACE CROP
# =========================================================

def generate_embedding(image):

    """
    Generate a 512-dimensional FaceNet512
    embedding from an already detected face crop.

    detector_backend='skip' is intentional because
    MTCNN has already detected and cropped the face.
    """

    result = DeepFace.represent(
        img_path=image,
        model_name=MODEL_NAME,
        detector_backend=EMBEDDING_DETECTOR,
        enforce_detection=False
    )

    if not result:
        raise ValueError(
            "Face embedding could not be generated."
        )

    embedding = np.asarray(
        result[0]["embedding"],
        dtype=np.float32
    )

    if len(embedding) != 512:
        raise ValueError(
            f"Expected 512 dimensions, got {len(embedding)}"
        )

    # Normalize embedding
    norm = np.linalg.norm(embedding)

    if norm == 0:
        raise ValueError(
            "Invalid zero embedding."
        )

    embedding = embedding / norm

    return embedding


# =========================================================
# RECOGNIZE ONE FACE
# =========================================================

def recognize_face_crop(face_crop, students):

    """
    Recognize one already-detected REAL face.

    Anti-spoofing must happen BEFORE this function.
    """

    query_embedding = generate_embedding(
        face_crop
    )

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

            # Normalize stored embedding
            norm = np.linalg.norm(
                stored_embedding
            )

            if norm == 0:
                continue

            stored_embedding = (
                stored_embedding / norm
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

    # MATCH
    if (
        best_student is not None
        and best_distance <= DISTANCE_THRESHOLD
    ):

        return {
            "matched": True,
            "student": best_student,
            "distance": best_distance
        }

    # UNKNOWN
    return {
        "matched": False,
        "student": None,
        "distance": (
            best_distance
            if best_distance != float("inf")
            else None
        )
    }


# =========================================================
# MULTI-FACE + ANTI-SPOOF RECOGNITION
# =========================================================

def recognize_faces_in_frame(image, students):

    """
    Complete classroom recognition pipeline.

    1. Detect all faces using MTCNN.
    2. Run anti-spoofing.
    3. Require minimum 3 detected faces.
    4. Recognize REAL faces using FaceNet512.
    5. Return results for every detected face.

    IMPORTANT:
    SPOOF faces NEVER reach FaceNet recognition.
    """

    # =====================================================
    # DETECT ALL FACES + ANTI-SPOOF
    # =====================================================

    results = DeepFace.extract_faces(
        img_path=image,
        detector_backend="mtcnn",
        enforce_detection=False,
        align=True,
        anti_spoofing=True
    )

    face_count = len(results)

    print(
        f"Faces detected: {face_count}"
    )

    # =====================================================
    # MINIMUM FACE REQUIREMENT
    # =====================================================

    if face_count < MIN_FACES_REQUIRED:

        return {
            "success": True,
            "ready": False,
            "minimum_faces": MIN_FACES_REQUIRED,
            "face_count": face_count,
            "message": (
                f"At least {MIN_FACES_REQUIRED} "
                f"faces are required."
            ),
            "faces": []
        }

    recognized_faces = []

    # =====================================================
    # PROCESS EVERY FACE
    # =====================================================

    for index, face_data in enumerate(results):

        try:

            area = face_data.get(
                "facial_area",
                {}
            )

            x = int(area.get("x", 0))
            y = int(area.get("y", 0))
            w = int(area.get("w", 0))
            h = int(area.get("h", 0))

            # -------------------------------------------------
            # PREVENT INVALID COORDINATES
            # -------------------------------------------------

            x = max(0, x)
            y = max(0, y)

            image_height = image.shape[0]
            image_width = image.shape[1]

            x2 = min(
                image_width,
                x + w
            )

            y2 = min(
                image_height,
                y + h
            )

            if x2 <= x or y2 <= y:

                continue

            # =================================================
            # ANTI-SPOOF RESULT
            # =================================================

            is_real = face_data.get(
                "is_real",
                False
            )

            antispoof_score = face_data.get(
                "antispoof_score",
                0.0
            )

            # =================================================
            # SPOOF
            # =================================================

            if not is_real:

                print(
                    f"Face {index + 1}: SPOOF "
                    f"score={antispoof_score:.3f}"
                )

                recognized_faces.append({

                    "face_index":
                        index + 1,

                    "x":
                        x,

                    "y":
                        y,

                    "x2":
                        x2,

                    "y2":
                        y2,

                    "is_real":
                        False,

                    "antispoof_score":
                        float(antispoof_score),

                    "matched":
                        False,

                    "student":
                        None,

                    "distance":
                        None,

                    "status":
                        "SPOOF"
                })

                # VERY IMPORTANT
                #
                # Do not run FaceNet.
                # Do not recognize.
                # Do not mark attendance.

                continue

            # =================================================
            # REAL FACE
            # =================================================

            print(
                f"Face {index + 1}: REAL "
                f"score={antispoof_score:.3f}"
            )

            face_crop = image[
                y:y2,
                x:x2
            ]

            if face_crop.size == 0:

                continue

            # =================================================
            # FACE RECOGNITION
            # =================================================

            recognition = recognize_face_crop(
                face_crop,
                students
            )

            # =================================================
            # MATCH
            # =================================================

            if recognition["matched"]:

                student = recognition["student"]

                print(
                    f"Face {index + 1}: "
                    f"MATCH → "
                    f"{student.name} "
                    f"distance="
                    f"{recognition['distance']:.4f}"
                )

                recognized_faces.append({

                    "face_index":
                        index + 1,

                    "x":
                        x,

                    "y":
                        y,

                    "x2":
                        x2,

                    "y2":
                        y2,

                    "is_real":
                        True,

                    "antispoof_score":
                        float(antispoof_score),

                    "matched":
                        True,

                    "student":
                        student,

                    "distance":
                        recognition["distance"],

                    "status":
                        "MATCHED"
                })

            # =================================================
            # UNKNOWN REAL PERSON
            # =================================================

            else:

                print(
                    f"Face {index + 1}: "
                    f"UNKNOWN "
                    f"distance="
                    f"{recognition['distance']}"
                )

                recognized_faces.append({

                    "face_index":
                        index + 1,

                    "x":
                        x,

                    "y":
                        y,

                    "x2":
                        x2,

                    "y2":
                        y2,

                    "is_real":
                        True,

                    "antispoof_score":
                        float(antispoof_score),

                    "matched":
                        False,

                    "student":
                        None,

                    "distance":
                        recognition["distance"],

                    "status":
                        "UNKNOWN"
                })

        except Exception as error:

            print(
                f"Face {index + 1} processing error:",
                error
            )

    # =====================================================
    # RETURN
    # =====================================================

    return {

        "success":
            True,

        "ready":
            True,

        "minimum_faces":
            MIN_FACES_REQUIRED,

        "face_count":
            face_count,

        "message":
            "Face recognition completed.",

        "faces":
            recognized_faces
    }


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================

def recognize_face(image, students):

    """
    Original single-face recognition function.

    Kept so other existing code does not immediately break.

    For the actual classroom attendance system,
    use recognize_faces_in_frame().
    """

    query_embedding = generate_embedding(
        image
    )

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

            norm = np.linalg.norm(
                stored_embedding
            )

            if norm == 0:
                continue

            stored_embedding = (
                stored_embedding / norm
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

            "matched":
                True,

            "student":
                best_student,

            "distance":
                best_distance
        }

    return {

        "matched":
            False,

        "student":
            None,

        "distance":
            (
                best_distance
                if best_distance != float("inf")
                else None
            )
    }