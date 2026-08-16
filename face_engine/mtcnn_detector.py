import cv2
from mtcnn import MTCNN


# -----------------------------
# Load detectors
# -----------------------------

haar = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

mtcnn = MTCNN()


# -----------------------------
# Start camera
# -----------------------------

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open camera.")
    exit()

print("Hybrid face detection started.")
print("Press Q to quit.")


while True:

    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read frame.")
        break

    # -----------------------------
    # STEP 1: Haar pre-filter
    # -----------------------------

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    haar_faces = haar.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )

    # -----------------------------
    # STEP 2: Run MTCNN only when
    # Haar detects a possible face
    # -----------------------------

    if len(haar_faces) > 0:

        # MTCNN expects RGB, while OpenCV uses BGR
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        detections = mtcnn.detect_faces(rgb_frame)

        for detection in detections:

            x, y, w, h = detection["box"]

            # Prevent negative coordinates
            x = max(0, x)
            y = max(0, y)

            confidence = detection["confidence"]

            # -----------------------------
            # MTCNN bounding box
            # -----------------------------

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"MTCNN: {confidence * 100:.1f}%",
                (x, max(25, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            # -----------------------------
            # Facial landmarks
            # -----------------------------

            keypoints = detection["keypoints"]

            for point_name, point in keypoints.items():

                px, py = point

                cv2.circle(
                    frame,
                    (px, py),
                    4,
                    (0, 0, 255),
                    -1
                )

                cv2.putText(
                    frame,
                    point_name,
                    (px + 5, py),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.35,
                    (0, 0, 255),
                    1
                )

    # -----------------------------
    # Display information
    # -----------------------------

    cv2.putText(
        frame,
        f"Haar Faces: {len(haar_faces)}",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "Haar -> MTCNN",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "Smart Attendance - Hybrid Detection",
        frame
    )

    # Quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()