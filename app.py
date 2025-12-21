import streamlit as st
import face_recognition # The main library for detecting and recognizing faces
import cv2 # OpenCV library for image processing
import numpy as np # Library for numerical operations (math for images)
import os # Library to interact with the operating system (reading files/folders)
from datetime import datetime # Library to work with dates and times
import av # Library for working with audio/video (used by WebRTC)

# Try to import streamlit_webrtc for real-time video functionality
# If it's not installed, we catch the error to prevent the app from crashing entirely
try:
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
except ImportError:
    st.error("streamlit-webrtc is not installed. Please add it to requirements.txt")

# ==========================================
# 1. Configuration & Constants
# ==========================================
# Set up the page layout and title
st.set_page_config(page_title="Attendance System", page_icon="📍", layout="wide")

# Define paths to folders where we store images
PATH_IMAGES = 'Images_Attendance' # Folder for registered users
PATH_STRANGERS = 'Strangers' # Folder to save unknown faces

# Constants for "Liveness" detection (to prevent cheating with photos)
EYE_AR_THRESH = 0.25  # Threshold: If eye aspect ratio is below this, it's a blink
EYE_AR_CONSEC_FRAMES = 2 # How many frames the eyes must be closed to count as a blink
LIVENESS_TIMEOUT = 5.0 # How long (seconds) "Verified" status lasts before you need to blink again

# Create folders if they don't exist yet
if not os.path.exists(PATH_IMAGES): os.makedirs(PATH_IMAGES)
if not os.path.exists(PATH_STRANGERS): os.makedirs(PATH_STRANGERS)

# ==========================================
# 2. Helper Functions (Shared Logic)
# ==========================================

# @st.cache_resource is a Streamlit decorator.
# It tells Streamlit: "Run this function ONCE and save the result."
# We use it here because loading 100+ images takes time. We don't want to do it every refresh.
# WE WILL CLEAR THIS CACHE WHEN A NEW USER REGISTERS.
@st.cache_resource
def load_encodings():
    """
    Reads all images in the 'Images_Attendance' folder and creates 'encodings' for them.
    An 'encoding' is a list of 128 numbers that essentially describes the face features.
    """
    encodings_list = [] # List to store the face data
    names_list = [] # List to store the names corresponding to the faces
    
    # Get a list of all files in the folder
    file_list = os.listdir(PATH_IMAGES)
    
    for cl in file_list:
        # Check if the file is an image
        if cl.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = f'{PATH_IMAGES}/{cl}'
            
            # Read the image using OpenCV
            curImg = cv2.imread(img_path)
            
            if curImg is not None:
                # Convert from BGR (OpenCV standard) to RGB (Face Recognition standard)
                curImg = cv2.cvtColor(curImg, cv2.COLOR_BGR2RGB)
                
                # Find face encoding
                # We assume there's only one face per profile picture [0]
                encodes = face_recognition.face_encodings(curImg)
                
                if len(encodes) > 0:
                    encodings_list.append(encodes[0])
                    
                    # Clean up the name (remove file extension and any extra tags like '_front')
                    # Example: "Elon_Musk.jpg" -> "Elon_Musk"
                    name_base = os.path.splitext(cl)[0]
                    names_list.append(name_base.split('_')[0] if '_' in name_base else name_base)
    
    st.toast(f"System Loaded: {len(names_list)} profiles found.", icon="✅")
    return encodings_list, names_list

def mark_attendance(name):
    """
    Checks if a user is already marked for today in 'Attendance.csv'.
    If not, it adds them to the file with the current timestamp.
    """
    filename = 'Attendance.csv'
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d') # Format: 2023-10-27
    time_str = now.strftime('%H:%M:%S')  # Format: 14:30:00

    # Create file if it doesn't exist
    if not os.path.exists(filename):
        with open(filename, 'w') as f: f.write("Name,Time,Date")

    # Read existing data to check duplicates
    try:
        with open(filename, 'r') as f: lines = f.readlines()
    except FileNotFoundError: lines = []

    # Check every line to see if this person is already marked TODAY
    for line in lines:
        entry = line.split(',')
        if len(entry) >= 3:
            # entry[0] is Name, entry[2] is Date
            if entry[0] == name and entry[2].strip() == today_str:
                return "Already Marked"

    # If not found, write the new entry
    with open(filename, 'a') as f:
        f.write(f'\n{name},{time_str},{today_str}')
    return "Marked"

def calculate_ear(eye_points):
    """
    Math function to calculate 'Eye Aspect Ratio' (EAR).
    It compares the vertical distance of the eye to the horizontal distance.
    Used to detect blinks (when vertical distance becomes typically small).
    """
    A = np.linalg.norm(eye_points[1] - eye_points[5]) # Vertical distance 1
    B = np.linalg.norm(eye_points[2] - eye_points[4]) # Vertical distance 2
    C = np.linalg.norm(eye_points[0] - eye_points[3]) # Horizontal distance
    return (A + B) / (2.0 * C)

# ==========================================
# 3. WebRTC Video Processor (Advanced Mode)
# ==========================================
# This class handles the video stream frame-by-frame for the "Real-Time" mode.
class FaceRecognitionProcessor(VideoProcessorBase):
    def __init__(self):
        # Load known faces when the processor starts
        self.known_encodings, self.known_names = load_encodings()
        
        # Variables for Blink/Liveness detection
        self.blink_counter = 0
        self.total_blinks = 0
        self.liveness_verified = False
        
    def transform(self, frame):
        """
        This function receives a video frame, processes it (draws boxes, recognizes faces),
        and returns the modified frame to be shown on screen.
        """
        # Convert the frame from WebRTC format to OpenCV format (numpy array)
        img = frame.to_ndarray(format="bgr24")
        
        # 1. Resize for Speed
        # We shrink the image to 1/4th size (0.5 * 0.5) to make processing faster
        imgS = cv2.resize(img, (0, 0), None, 0.50, 0.50)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
        
        # 2. Detect Faces and Generate Encodings for the current frame
        facesCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
        face_landmarks_list = face_recognition.face_landmarks(imgS, facesCurFrame)

        # 3. Liveness Logic (Did they blink?)
        if not self.liveness_verified:
            for face_landmarks in face_landmarks_list:
                leftEye = np.array(face_landmarks['left_eye'])
                rightEye = np.array(face_landmarks['right_eye'])
                # Calculate average Eye Aspect Ratio for both eyes
                avgEAR = (calculate_ear(leftEye) + calculate_ear(rightEye)) / 2.0
                
                # If eyes are closed (EAR < threshold)
                if avgEAR < EYE_AR_THRESH:
                    self.blink_counter += 1
                else:
                    # If eyes were closed for enough frames, count it as a blink
                    if self.blink_counter >= EYE_AR_CONSEC_FRAMES:
                        self.liveness_verified = True
                    self.blink_counter = 0
            
            # Show "Please Blink" message
            cv2.putText(img, "LIVENESS: PLEASE BLINK", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            # Show "Verified" message
            cv2.putText(img, "LIVENESS: VERIFIED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 4. Recognition Logic
        # Only process recognition if liveness is verified (or remove this check to recognize always)
        if self.liveness_verified:
            for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
                # Compare current face with all known faces
                matches = face_recognition.compare_faces(self.known_encodings, encodeFace)
                faceDis = face_recognition.face_distance(self.known_encodings, encodeFace)
                
                # Find the best match (smallest distance)
                matchIndex = np.argmin(faceDis)
                
                # Scale coordinates back up (since we resized by 0.5)
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 2, x2 * 2, y2 * 2, x1 * 2

                if matches[matchIndex]:
                    name = self.known_names[matchIndex].upper()
                    
                    # Mark Attendance logic
                    status = mark_attendance(name) 
                    
                    # Draw Green Box
                    color = (0, 255, 0)
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(img, f"{name} ({status})", (x1, y2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                else:
                    # Draw Red Box (Stranger)
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(img, "STRANGER", (x1, y2 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        return img

# ==========================================
# 4. Main Application Layout (Streamlit UI)
# ==========================================
st.title("📍 Facial Recognition Attendance System")

# Sidebar Menu
menu = ["Check In", "Register New User"]
choice = st.sidebar.selectbox("Menu", menu)

# ------------------------------------------------------------------
# FEATURE: REGISTER NEW USER
# ------------------------------------------------------------------
if choice == "Register New User":
    st.subheader("📝 Register New User")
    st.info("Why is this data temporary? | On Streamlit Cloud, data resets when the app sleeps. This is perfect for demos!")
    
    # 1. Input Name
    new_user_name = st.text_input("Enter Name (e.g., 'John_Doe'):")
    
    # 2. Input Photo
    st.write("Take a Selfie to Register:")
    img_file_buffer = st.camera_input("Register Camera")

    # 3. Save Logic
    if new_user_name and img_file_buffer is not None:
        # Create a valid filename (remove spaces, special chars)
        safe_name = "".join([c for c in new_user_name if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
        
        if st.button(f"Save Profile for {safe_name}"):
            # Convert raw bugger to image
            bytes_data = img_file_buffer.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            
            # Save to folder
            save_path = f"{PATH_IMAGES}/{safe_name}.jpg"
            cv2.imwrite(save_path, cv2_img)
            
            st.success(f"✅ Success! {safe_name} has been registered.")
            st.warning("Please switch to 'Check In' mode to test.")
            
            # CRITICAL: Clear cache so the system 're-learns' the new face immediately
            load_encodings.clear() 

# ------------------------------------------------------------------
# FEATURE: CHECK IN (Attendance Mode)
# ------------------------------------------------------------------
elif choice == "Check In":
    
    # Pre-load encodings (if not cached)
    with st.spinner("Loading Facial Data..."):
        try:
            knownEncodings, classNames = load_encodings()
        except Exception as e:
            st.error(f"Error loading encodings: {e}")
            knownEncodings = []
            classNames = []

    # Two Check-in Modes
    mode = st.radio("Select Method:", ["Simple Mode (Take Photo)", "Real-Time / Liveness (Video)"], horizontal=True)

    # --- MODE A: SIMPLE PHOTO ---
    if mode == "Simple Mode (Take Photo)":
        st.subheader("📸 Simple Check-in")
        st.caption("Best for mobile devices or slow internet.")
        
        img_buffer_checkin = st.camera_input("Take Attendance Photo")
        
        if img_buffer_checkin is not None:
             # Process the image similar to 'Register' but for recognizing
            bytes_data = img_buffer_checkin.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            
            # Standard resize and convert
            imgS = cv2.resize(cv2_img, (0, 0), None, 0.50, 0.50)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
            
            # Detect
            facesCurFrame = face_recognition.face_locations(imgS)
            encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
            
            if not facesCurFrame:
                st.warning("⚠️ No face detected. Please try again.")
            else:
                for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
                    if not knownEncodings:
                        st.error("System has no registered users yet.")
                        break
                        
                    matches = face_recognition.compare_faces(knownEncodings, encodeFace)
                    faceDis = face_recognition.face_distance(knownEncodings, encodeFace)
                    matchIndex = np.argmin(faceDis)
                    
                    if matches[matchIndex]:
                        name = classNames[matchIndex].upper()
                        status = mark_attendance(name)
                        st.balloons()
                        st.success(f"✅ Identity Verified: {name}")
                        st.info(f"Status: {status}")
                    else:
                        st.error("🚫 Unknown User. Please Register first.")

    # --- MODE B: REAL-TIME VIDEO ---
    else:
        st.subheader("🎥 Real-Time Check-in")
        st.caption("Requires Blink Detection for Security.")
        
        if not knownEncodings:
             st.error("⚠️ No users registered. Please go to 'Register New User' tab.")
        else:
            # Start WebRTC Streamer
            webrtc_streamer(
                key="realtime-attendance",
                video_processor_factory=FaceRecognitionProcessor, # Kept original processor
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                },
                media_stream_constraints={"video": True, "audio": False},
            )

    # VIEW ATTENDANCE TABLE
    st.divider()
    st.header("📋 Today's Attendance")
    
    if os.path.exists('Attendance.csv'):
        # Just reading the CSV as a text file for simplicity, 
        # but could use pandas.read_csv() for a nicer table.
        with open('Attendance.csv', 'r') as f:
            csv_data = f.read()
        
        col1, col2 = st.columns([2,1])
        with col1:
             st.text_area("CSV Log", csv_data, height=200)
        with col2:
             st.download_button("Download CSV", csv_data, "Attendance.csv", "text/csv")
    else:
        st.info("No attendance marked yet.")

