import cv2
from deepface import DeepFace

cap = cv2.VideoCapture(0)

print("Anti-spoofing test started.")
print("Press Q to quit.")

while True:

    ret, frame = cap.read()

    if not ret:
        break

    try:

        results = DeepFace.extract_faces(
            img_path=frame,
            detector_backend="mtcnn",
            enforce_detection=False,
            align=True,
            anti_spoofing=True
        )

        if results:

            for face in results:

                area = face["facial_area"]

                x = area["x"]
                y = area["y"]
                w = area["w"]
                h = area["h"]

                is_real = face.get(
                    "is_real",
                    False
                )

                score = face.get(
                    "antispoof_score",
                    0.0
                )

                if is_real:

                    color = (0, 255, 0)
                    label = f"REAL | {score:.3f}"

                else:

                    color = (0, 0, 255)
                    label = f"SPOOF | {score:.3f}"

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    label,
                    (x, max(25, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

                print(
                    f"is_real={is_real}, "
                    f"antispoof_score={score:.4f}"
                )

    except Exception as e:

        print("Error:", e)

    cv2.imshow(
        "Anti-Spoofing Test",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break

cap.release()

cv2.destroyAllWindows()