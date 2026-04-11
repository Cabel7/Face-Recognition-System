import face_recognition
import os
import pickle
import cv2
import numpy as np

def encode_faces():

    dataset = "dataset"
    encodings = []
    names = []

    # 🔥 Loop through each person folder
    for username in os.listdir(dataset):

        person_path = os.path.join(dataset, username)

        # Skip if not a folder
        if not os.path.isdir(person_path):
            continue

        # 🔥 Loop through images inside folder
        for file in os.listdir(person_path):

            path = os.path.join(person_path, file)

            img = cv2.imread(path)

            if img is None:
                print(f"Skipping invalid image: {path}")
                continue

            # Normalize image
            img = cv2.resize(img, (500, 500))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = np.array(img, dtype=np.uint8)

            try:
                face_encs = face_recognition.face_encodings(img)
            except Exception as e:
                print(f"Error processing {path}: {e}")
                continue

            if len(face_encs) == 0:
                print(f"No face found in {path}")
                continue

            # 🔥 Save encoding with correct name
            encodings.append(face_encs[0])
            names.append(username)   # IMPORTANT CHANGE

    os.makedirs("encodings", exist_ok=True)

    with open("encodings/encodings.pickle", "wb") as f:
        pickle.dump({"encodings": encodings, "names": names}, f)
        
    print("Total encodings:", len(encodings))
    print("Encoding complete")

if __name__ == "__main__":
    encode_faces()