import cv2 # The main library we use for Computer Vision (using the camera, drawing boxes)
import numpy as np # Library for math operations (images are just big grids of numbers!)
import face_recognition # The magic library that matches faces using AI
import os # Helps us read files and folders from your computer
from datetime import datetime # Helps us get the current date and time
import time # Helps us measure time (used for delays or cooldowns)

# ==========================================
# 1. Configuration & Constants
# ==========================================
# These are "Settings" for our app. changing them here changes how the app behaves.

PATH_IMAGES = 'Images_Attendance' # Folder where we store photos of Known People
PATH_STRANGERS = 'Strangers' # Folder where we automatically save photos of strangers

# Create the folders if they don't exist yet (so the code doesn't crash)
if not os.path.exists(PATH_IMAGES): os.makedirs(PATH_IMAGES)
if not os.path.exists(PATH_STRANGERS): os.makedirs(PATH_STRANGERS)

# LIVENESS Settings (To prevent someone from holding up a photo of you!)
EYE_AR_THRESH = 0.25  # How "closed" the eye needs to be to count as a blink
EYE_AR_CONSEC_FRAMES = 2 # How many frames (instants) the eye must be closed for
LIVENESS_TIMEOUT = 5.0 # How many seconds "Verified" status lasts before asking to blink again
STRANGER_COOLDOWN_SECONDS = 5.0 # Don't save 100 photos of the same stranger in 1 second. Wait 5s.

# Global Variables (Variables that change while the app is running)
COUNTER = 0 # Counts how many frames eyes have been closed
TOTAL_BLINKS = 0 # Total number of blinks detected
LIVENESS_VERIFIED = False # Is the person real? (True/False)
last_blink_time = 0 # Timestamp of the last valid blink
last_stranger_save_time = 0 # Timestamp of when we last saved a stranger's photo
last_attendance_status = {} # Dictionary to remember what status to show for each person

# ==========================================
# 2. Helper Functions
# ==========================================

def calculate_ear(eye_points):
    """
    Calculates "Eye Aspect Ratio" (EAR).
    Think of the eye as a polygon with 6 points. 
    This math formula checks if the polygon is "squashed" (closed eye) or "round" (open eye).
    """
    # Vertical distances (Height of eye)
    A = np.linalg.norm(eye_points[1] - eye_points[5])
    B = np.linalg.norm(eye_points[2] - eye_points[4])
    # Horizontal distance (Width of eye)
    C = np.linalg.norm(eye_points[0] - eye_points[3])
    # The Ratio
    ear = (A + B) / (2.0 * C)
    return ear

def markAttendance(name):
    """
    This function opens the 'Attendance.csv' file and adds the person's name 
    if they haven't been marked present today.
    """
    filename = 'Attendance.csv'
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d') # e.g. "2023-12-25"
    time_str = now.strftime('%H:%M:%S')  # e.g. "09:00:00"

    # If file doesn't exist, create it with Headers
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write("Name,Time,Date")

    # Read the file to see who is already here
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except:
        lines = []

    # Check for duplicates
    for line in lines:
        entry = line.split(',')
        # Check if the line has data and matches the Name + Today's Date
        if len(entry) >= 3:
            existing_name = entry[0]
            existing_date = entry[2].strip()
            if existing_name == name and existing_date == today_str:
                return "ALREADY_LOGGED" 

    # If we get here, they are not duplicated. Write them down!
    try:
        with open(filename, 'a') as f: # 'a' means Append (add to end)
            f.write(f'\n{name},{time_str},{today_str}')
        print(f"✅ CSV WRITE SUCCESS: {name} at {time_str}")
        return "MARKED"
    except Exception as e:
        print(f"❌ CSV WRITE ERROR: {e}")
        return "ERROR"

# ==========================================
# 3. Load Images (The "Training" Phase)
# ==========================================
# The app learns faces right when it starts up.
known_face_encodings = []
known_face_names = []
print(f"Loading images from '{PATH_IMAGES}'...")

# Loop through every file in the folder
for cl in os.listdir(PATH_IMAGES):
    if cl.lower().endswith(('.png', '.jpg', '.jpeg')):
        img_path = f'{PATH_IMAGES}/{cl}'
        curImg = cv2.imread(img_path)
        if curImg is None: continue
        
        # Convert color layout from BGR (OpenCV) to RGB (Face Recognition)
        curImg = cv2.cvtColor(curImg, cv2.COLOR_BGR2RGB)
        
        # Detect face and encode it
        encodes = face_recognition.face_encodings(curImg)
        
        if len(encodes) > 0:
            face_encoding = encodes[0] # Take the first face found
            
            # Smart Name Cleaning
            # Turns "Obama_front.jpg" into just "Obama"
            name_base = os.path.splitext(cl)[0]
            if '_' in name_base:
                parts = name_base.split('_')
                last_part = parts[-1].lower()
                # If filename ends with direction like 'Left', ignore that part
                keywords = ['front', 'side', 'down', 'up', 'left', 'right', 'profile']
                if any(k in last_part for k in keywords):
                    name = "_".join(parts[:-1]) 
                else:
                    name = name_base
            else:
                name = name_base
            
            known_face_encodings.append(face_encoding)
            known_face_names.append(name)
            print(f"Encoded: {name}")

print(f"\nsuccesfully loaded {len(known_face_encodings)} templates.")

# ==========================================
# 4. Main Webcam Loop (The "Action" Phase)
# ==========================================
# 0 usually means the built-in webcam.
cap = cv2.VideoCapture(0)

print("\nControls:")
print("  [q] Quit")
print("  [o] OVERRIDE (Skip Blink & Mark Attendance)")
print("  [c] CLEAR Liveness (Reset)")

while True:
    # Read one frame/image from camera
    success, img = cap.read()
    if not success: break

    # OPTIMIZATION: Reduce image size by half to speed up processing
    imgS = cv2.resize(img, (0, 0), None, 0.50, 0.50)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Detect faces in current frame
    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
    # Detect landmarks (eyes, nose, etc) for liveness
    face_landmarks_list = face_recognition.face_landmarks(imgS, facesCurFrame)

    # Listen for Keyboard input
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): break # Quit
    if key == ord('o'): # Manual Override (Cheat Code)
        LIVENESS_VERIFIED = True 
        last_blink_time = time.time()
        print("MANUAL OVERRIDE ENABLED")
    if key == ord('c'): # Clear verification
        LIVENESS_VERIFIED = False
        print("Liveness RESET")

    # LIVENESS LOGIC
    if not LIVENESS_VERIFIED:
        # Check every face
        for face_landmarks in face_landmarks_list:
            leftEye = np.array(face_landmarks['left_eye'])
            rightEye = np.array(face_landmarks['right_eye'])
            # Check blink
            avgEAR = (calculate_ear(leftEye) + calculate_ear(rightEye)) / 2.0
            
            if avgEAR < EYE_AR_THRESH:
                COUNTER += 1 # Eyes are closed
            else:
                if COUNTER >= EYE_AR_CONSEC_FRAMES: # Eyes were closed long enough
                    TOTAL_BLINKS += 1
                    LIVENESS_VERIFIED = True
                    last_blink_time = time.time() # Remember when they blinked
                COUNTER = 0 # Reset counter if eyes open
    else:
        # Reset liveness if too much time passed
        if time.time() - last_blink_time > LIVENESS_TIMEOUT:
            LIVENESS_VERIFIED = False

    # DRAW UI (The banner at the top)
    cv2.rectangle(img, (0,0), (600, 100), (0,0,0), cv2.FILLED) # Black background
    
    if LIVENESS_VERIFIED:
        cv2.putText(img, "LIVENESS: VERIFIED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    else:
        cv2.putText(img, "LIVENESS: PLEASE BLINK", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(img, "(or press 'o' to override)", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # RECOGNITION LOGIC (Match faces)
    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        # Compare Face
        matches = face_recognition.compare_faces(known_face_encodings, encodeFace)
        faceDis = face_recognition.face_distance(known_face_encodings, encodeFace)
        
        # Best match is the one with smallest distance
        matchIndex = np.argmin(faceDis)
        matchScore = faceDis[matchIndex] if len(faceDis) > 0 else 1.0

        # Scale coordinates back up (x2) because we shrunk image by 0.5 earlier
        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1 * 2, x2 * 2, y2 * 2, x1 * 2

        if matches[matchIndex]:
            name = known_face_names[matchIndex].upper()
            
            # Draw Green Box
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"Score: {round(matchScore, 2)}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Mark Attendance ONLY if Liveness is verified
            if LIVENESS_VERIFIED:
                status = markAttendance(name)
                
                # Update status message to show on screen
                if status == "MARKED":
                    last_attendance_status[name] = f"SUCCESS: {name} CHECKED IN"
                elif status == "ALREADY_LOGGED":
                    last_attendance_status[name] = f"INFO: {name} ALREADY HERE"
                elif status == "ERROR":
                    last_attendance_status[name] = "ERROR: Could Not Write CSV"
            
            # Show the status message
            if name in last_attendance_status:
                status_text = last_attendance_status[name]
                color = (0, 255, 255) if "INFO" in status_text else (0, 255, 0)
                if "ERROR" in status_text: color = (0, 0, 255)
                
                cv2.putText(img, status_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            elif not LIVENESS_VERIFIED:
                 cv2.putText(img, f"Found: {name} - Waiting for Blink...", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        else:
            # UNKNOWN PERSON (Stranger)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(img, f"STRANGER (Score: {round(matchScore, 2)})", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Intruder Alert: Save their photo
            if time.time() - last_stranger_save_time > STRANGER_COOLDOWN_SECONDS:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{PATH_STRANGERS}/Unknown_{timestamp}.jpg"
                h, w, c = img.shape
                # Crop the face
                face_img = img[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                if face_img.size > 0:
                    cv2.imwrite(filename, face_img)
                    print(f"Captured: {filename}")
                    last_stranger_save_time = time.time()
                    # Flash blue box to show capture
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 4)

    # Show the final image window
    cv2.imshow('Facial Recognition Attendance', img)

# Cleanup when done
cap.release()
cv2.destroyAllWindows()
