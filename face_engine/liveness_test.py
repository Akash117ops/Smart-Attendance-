import cv2
from mtcnn import MTCNN
import numpy as np

detector = MTCNN()
cap = cv2.VideoCapture(0)

positions = []
WINDOW = 20
MOVEMENT_THRESHOLD = 20

print("Liveness test started.")
print("Move your head slightly left/right.")
print("Press Q to quit.")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = detector.detect_faces(rgb)

    status = "NO FACE"

    if faces:
        # Select largest detected face
        face = max(faces, key=lambda f: f["box"][2] * f["box"][3])

        x, y, w, h = face["box"]

        # Face centre
        center_x = x + w // 2
        center_y = y + h // 2

        positions.append((center_x, center_y))

        if len(positions) > WINDOW:
            positions.pop(0)

        if len(positions) >= WINDOW:
            movement = np.ptp(np.array(positions), axis=0)
            total_movement = movement[0] + movement[1]

            if total_movement > MOVEMENT_THRESHOLD:
                status = "LIVE"
            else:
                status = "MOVE HEAD"

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

    cv2.putText(
        frame,
        f"Liveness: {status}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.imshow("Smart Attendance - Liveness Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()