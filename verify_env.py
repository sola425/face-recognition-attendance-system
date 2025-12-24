import face_recognition
import cv2
import os
import numpy as np

print("--- Environment Verification ---")

# 1. Check Libraries
try:
    print(f"OpenCV Version: {cv2.__version__}")
    print(f"Face Recognition installed.")
except ImportError as e:
    print(f"CRITICAL: Library missing: {e}")

# 2. Check Images Folder
PATH_IMAGES = 'Images_Attendance'
if not os.path.exists(PATH_IMAGES):
    print(f"CRITICAL: {PATH_IMAGES} does not exist!")
else:
    files = [f for f in os.listdir(PATH_IMAGES) if f.endswith(('.jpg', '.jpeg', '.png'))]
    print(f"Found {len(files)} images.")
    
    # 3. Test Load & Encode on first image
    if files:
        test_file = files[0]
        print(f"Testing encoding on {test_file}...")
        try:
            path = os.path.join(PATH_IMAGES, test_file)
            img = cv2.imread(path)
            if img is None:
                print("Failed to read image with cv2.")
            else:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                encs = face_recognition.face_encodings(rgb)
                if encs:
                    print(f"SUCCESS: Generated {len(encs)} encodings for {test_file}.")
                else:
                    print(f"WARNING: No face found in {test_file}.")
        except Exception as e:
            print(f"ERROR processing image: {e}")

print("--- End Verification ---")
