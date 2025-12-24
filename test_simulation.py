import cv2
import face_recognition
import os
import numpy as np
import pandas as pd
from datetime import datetime

# Configuration
PATH_IMAGES = 'Images_Attendance'
FILE_DB = 'Attendance.csv'
TEST_IMAGE_NAME = 'Adeboye_Bamkole_Front.jpg' # We test if this person can recognize themselves

print("--- STARTING SIMULATION ---")

# 1. Load Known Faces (Logic from app.py)
print(f"1. Loading Database from {PATH_IMAGES}...")
known_encodings = []
known_names = []

if not os.path.exists(PATH_IMAGES):
    print("ERROR: Images folder not found!")
    exit()

files = [f for f in os.listdir(PATH_IMAGES) if f.endswith(('.jpg', '.jpeg', '.png'))]
print(f"   Found {len(files)} files.")

for file in files:
    try:
        img_path = os.path.join(PATH_IMAGES, file)
        img = cv2.imread(img_path)
        if img is None:
            continue
            
        # Resize logic
        height, width = img.shape[:2]
        if width > 800:
            scale = 800 / width
            img = cv2.resize(img, (0, 0), fx=scale, fy=scale)
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Rotation check logic
        results = face_recognition.face_encodings(img_rgb)
        if not results:
            img_cw = cv2.rotate(img_rgb, cv2.ROTATE_90_CLOCKWISE)
            results = face_recognition.face_encodings(img_cw)
        if not results:
            img_ccw = cv2.rotate(img_rgb, cv2.ROTATE_90_COUNTERCLOCKWISE)
            results = face_recognition.face_encodings(img_ccw)

        if results:
            known_encodings.append(results[0])
            name = os.path.splitext(file)[0].replace('_', ' ')
            known_names.append(name)
            # print(f"   + Loaded {name}")
    except Exception as e:
        print(f"   - Error loading {file}: {e}")

print(f"   Database Loaded: {len(known_encodings)} faces.")

# 2. Simulate Input Image
print(f"\n2. Simulating Camera Input with {TEST_IMAGE_NAME}...")
test_path = os.path.join(PATH_IMAGES, TEST_IMAGE_NAME)
if not os.path.exists(test_path):
    print(f"ERROR: Test image {TEST_IMAGE_NAME} not found!")
    exit()

input_img = cv2.imread(test_path)
# Resize input
h, w = input_img.shape[:2]
if w > 800:
    scale = 800 / w
    input_img = cv2.resize(input_img, (0, 0), fx=scale, fy=scale)

input_rgb = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)

# 3. Detect & Match
print("3. Running Recognition...")
face_locs = face_recognition.face_locations(input_rgb)
face_encs = face_recognition.face_encodings(input_rgb, face_locs)

print(f"   Detected {len(face_encs)} faces in input.")

if not face_encs:
    print("WARNING: No faces detected in test image.")

for enc in face_encs:
    face_dis = face_recognition.face_distance(known_encodings, enc)
    match_index = np.argmin(face_dis)
    min_dist = face_dis[match_index]
    
    print(f"   Closest match: {known_names[match_index]} with distance {min_dist:.4f}")
    
    matches = face_recognition.compare_faces(known_encodings, enc, tolerance=0.6)
    if matches[match_index]:
        name = known_names[match_index]
        print(f"   SUCCESS: Recognized {name}!")
        
        # 4. Mark Attendance
        print(f"\n4. Marking Attendance for {name}...")
        
        if not os.path.exists(FILE_DB):
             df = pd.DataFrame(columns=['Name', 'Time', 'Date'])
        else:
             df = pd.read_csv(FILE_DB)
             
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        if df.empty:
             is_marked = False
        else:
             is_marked = ((df['Name'] == name) & (df['Date'] == date_str)).any()

        if not is_marked:
            new_entry = pd.DataFrame({'Name': [name], 'Time': [time_str], 'Date': [date_str]})
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(FILE_DB, index=False)
            print(f"   Attendance Marked: {name} at {time_str}")
        else:
            print("   Attendance already marked for today.")
            
    else:
        print("   FAILED: Match distance too high.")

print("\n--- SIMULATION COMPLETE ---")
