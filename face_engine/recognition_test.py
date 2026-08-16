from deepface import DeepFace
import numpy as np

IMAGE_1 = "dataset/test/akash1.jpg"
IMAGE_2 = "dataset/test/akash2.jpg"


def get_embedding(image_path):
    result = DeepFace.represent(
        img_path=image_path,
        model_name="Facenet512",
        detector_backend="mtcnn",
        enforce_detection=True
    )

    embedding = np.array(result[0]["embedding"])

    return embedding


print("Generating embedding for image 1...")
embedding1 = get_embedding(IMAGE_1)

print("Generating embedding for image 2...")
embedding2 = get_embedding(IMAGE_2)

print()
print("Embedding 1 dimensions:", len(embedding1))
print("Embedding 2 dimensions:", len(embedding2))


# Cosine distance
dot_product = np.dot(embedding1, embedding2)

norm1 = np.linalg.norm(embedding1)
norm2 = np.linalg.norm(embedding2)

cosine_similarity = dot_product / (norm1 * norm2)

cosine_distance = 1 - cosine_similarity


print()
print("Cosine Similarity:", round(cosine_similarity, 4))
print("Cosine Distance:", round(cosine_distance, 4))


if cosine_distance < 0.60:
    print("RESULT: MATCH")
else:
    print("RESULT: NOT A MATCH")