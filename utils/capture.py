
import cv2
import numpy as np
import os

def capture_face(name):

    os.makedirs("dataset", exist_ok=True)

    user_dir = f"dataset/{name.lower()}"
    os.makedirs(user_dir, exist_ok=True)

    path = f"{user_dir}/1.jpg"
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cam.isOpened():
        print("Camera not opening")
        return False

    while True:
        ret, frame = cam.read()

        if not ret or frame is None:
            print("Invalid frame")
            continue

        # ✅ NumPy fix
        frame = np.asarray(frame, dtype=np.uint8)
        frame = frame.copy()

        cv2.imshow("Press SPACE to capture", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == 32:
            success = cv2.imwrite(path, frame)

            if success:
                print(f"Saved {path}")
            else:
                print("Save failed")

            break

        elif key == 27:
            break

    cam.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)

    return True