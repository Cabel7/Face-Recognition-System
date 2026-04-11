import cv2
import face_recognition
import pickle
import os
from datetime import datetime
import sqlite3
import time
import numpy as np

def recognize_from_frame(frame):
    import numpy as np

    data = pickle.loads(open("encodings/encodings.pickle", "rb").read())

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    faces = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, faces)

    for encoding in encodings:
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        face_distances = face_recognition.face_distance(data["encodings"], encoding)

        best_match_index = np.argmin(face_distances)

        if matches[best_match_index] and face_distances[best_match_index] < 0.5:
            return data["names"][best_match_index]

    return None