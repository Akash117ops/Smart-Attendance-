import pickle
import numpy as np
from deepface import DeepFace


def generate_student_embedding(image_paths):

    embeddings = []

    for image_path in image_paths:

        print(f"Processing: {image_path}")

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

            if len(embedding) != 512:
                raise ValueError(
                    f"Invalid embedding size: {len(embedding)}"
                )

            embeddings.append(embedding)

            print("Embedding generated: 512")

        except Exception as e:
            print(
                f"Skipped {image_path}: {e}"
            )

    if not embeddings:
        raise ValueError(
            "No valid face images were processed."
        )

    # Average embeddings
    final_embedding = np.mean(
        embeddings,
        axis=0
    )

    # Normalize
    norm = np.linalg.norm(
        final_embedding
    )

    if norm == 0:
        raise ValueError(
            "Invalid zero embedding."
        )

    final_embedding = (
        final_embedding / norm
    )

    return pickle.dumps(
        final_embedding
    ), len(embeddings)