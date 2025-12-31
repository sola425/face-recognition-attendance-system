import streamlit as st
import cv2
import numpy as np
import face_recognition
import os
import pandas as pd
from datetime import datetime
import tempfile
import shutil
import glob

# --- CONFIGURATION ---
st.set_page_config(page_title="AI Attendance System", layout="centered", page_icon="📍")

# --- STORAGE SETUP ---
DEFAULT_IMG_FOLDER = 'Images_Attendance'
DEFAULT_CSV_FILE = 'attendance_log.csv'

@st.cache_resource
def setup_storage():
    """
    Sets up the storage environment.
    - Resolves absolute path to find the Repo folder `Images_Attendance`.
    - Copies files to Temp if Read-Only.
    """
    is_temp = False
    img_folder = DEFAULT_IMG_FOLDER
    csv_file = DEFAULT_CSV_FILE
    
    # 1. Resolve Absolute Repo Path
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    repo_img_path = os.path.join(curr_dir, DEFAULT_IMG_FOLDER)

    copied_count = 0

    try:
        # 2. Try to write to Default
        os.makedirs(repo_img_path, exist_ok=True)
        test_file = os.path.join(repo_img_path, '.test')
        with open(test_file, 'w') as f:
             f.write('test')
        os.remove(test_file)
        
        # Check CSV
        if not os.path.exists(DEFAULT_CSV_FILE):
             with open(DEFAULT_CSV_FILE, 'w') as f:
                 f.write('')
                 
    except OSError:
        # READ-ONLY: Switch to Temp
        is_temp = True
        temp_dir = tempfile.mkdtemp(prefix="face_rec_app_")
        img_folder = temp_dir
        csv_file = os.path.join(temp_dir, 'attendance_log.csv')
        
        # 3. SYNC: Copy from Repo -> Temp
        if os.path.exists(repo_img_path):
            # grab both jpg and png
            files = glob.glob(os.path.join(repo_img_path, "*")) 
            for s in files:
                if s.lower().endswith(('.jpg', '.jpeg', '.png')):
                     d = os.path.join(img_folder, os.path.basename(s))
                     try:
                         shutil.copy2(s, d)
                         copied_count += 1
                     except Exception:
                         pass

    return img_folder, csv_file, is_temp, copied_count

IMG_FOLDER, CSV_FILE, IS_TEMP_STORAGE, COPIED_COUNT = setup_storage()

# Ensure CSV
if not os.path.exists(CSV_FILE):
    try:
        pd.DataFrame(columns=['Name', 'Time', 'Date']).to_csv(CSV_FILE, index=False)
    except:
        pass

# --- HELPER FUNCTIONS ---

@st.cache_data
def load_registered_faces():
    known_encodings = []
    known_names = []
    
    if os.path.exists(IMG_FOLDER):
        files = [f for f in os.listdir(IMG_FOLDER) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        for file in files:
            path = os.path.join(IMG_FOLDER, file)
            try:
                img = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(img)
                if encodings:
                    known_encodings.append(encodings[0])
                    name = os.path.splitext(file)[0].replace('_', ' ')
                    known_names.append(name)
            except Exception:
                pass
    return known_encodings, known_names

def mark_attendance(name):
    try:
        df = pd.read_csv(CSV_FILE)
    except:
        df = pd.DataFrame(columns=['Name', 'Time', 'Date'])

    now = datetime.now()
    today_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M:%S')

    if not df.empty:
        already_present = df[(df['Name'] == name) & (df['Date'] == today_date)]
        if not already_present.empty:
            return False, "Already checked in today!"

    new_entry = pd.DataFrame({'Name': [name], 'Time': [current_time], 'Date': [today_date]})
    try:
        new_entry.to_csv(CSV_FILE, mode='a', header=False, index=False)
        return True, f"Welcome, {name}! Attendance marked."
    except Exception as e:
        return False, f"Error saving attendance: {e}"

# --- MAIN UI ---

st.title("📍 AI Face Attendance")

# Sidebar Info
if IS_TEMP_STORAGE:
    st.sidebar.warning(f"⚠️ Read-Only Mode. Copied {COPIED_COUNT} images from repo.")
else:
    st.sidebar.success(f"✅ Persistent Mode. Accessing {IMG_FOLDER}")

with st.sidebar.expander("🛠️ Debug Info"):
    if os.path.exists(IMG_FOLDER):
        files = os.listdir(IMG_FOLDER)
        st.write(f"Images in buffer ({len(files)}):")
        st.write(files)

menu = ["Check In", "Register New User", "View Logs"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Register New User":
    st.subheader("📝 Register New Face")
    
    # 1. Initialize State for Image BYTES
    if 'reg_img_bytes' not in st.session_state:
        st.session_state.reg_img_bytes = None

    new_name = st.text_input("Enter Full Name")
    
    # 2. Input Method
    tab1, tab2 = st.tabs(["📸 Camera", "📂 Upload"])
    
    with tab1:
        cam_input = st.camera_input("Take a Selfie", key="camera_widget")
        if cam_input:
            # SAVE BYTES IMMEDIATELY
            st.session_state.reg_img_bytes = cam_input.getvalue()
    
    with tab2:
        up_input = st.file_uploader("Upload Image", type=['jpg','png','jpeg'], key="upload_widget")
        if up_input:
            st.session_state.reg_img_bytes = up_input.getvalue()

    # 3. Validation & SAVE
    if st.button("Save User"):
        if not new_name:
            st.error("Please enter a name first.")
        elif st.session_state.reg_img_bytes is None:
             st.error("Please take a photo or upload one first.")
        else:
            status = st.status("Processing registration...", expanded=True)
            try:
                status.write("1. Reading image data...")
                # Decode from Session State Bytes
                bytes_data = st.session_state.reg_img_bytes
                cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                
                h, w = cv2_img.shape[:2]
                status.write(f"2. Image size: {w}x{h}")
                
                # Resize if massive (4k)
                if w > 800:
                    scale = 800 / w
                    new_h = int(h * scale)
                    cv2_img = cv2.resize(cv2_img, (800, new_h))
                    status.write(f"3. Resized to {800}x{new_h}")
                
                rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
                
                status.write("4. Detecting face...")
                # Use standard model first, it's more accurate than hog for static images
                face_locations = face_recognition.face_locations(rgb_img)
                
                if len(face_locations) == 1:
                    status.write("5. Encoding face...")
                    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
                    
                    if face_encodings:
                        filename = f"{new_name.replace(' ', '_')}.jpg"
                        path = os.path.join(IMG_FOLDER, filename)
                        cv2.imwrite(path, cv2_img)
                        
                        status.update(label="Success!", state="complete", expanded=False)
                        st.success(f"User '{new_name}' registered!")
                        
                        # Clear state
                        st.session_state.reg_img_bytes = None
                        st.cache_data.clear() 
                    else:
                        status.update(label="Encoding Error", state="error")
                        st.error("Face detected but could not be encoded. Try better lighting.")
                elif len(face_locations) == 0:
                     status.update(label="No Face", state="error")
                     st.error("❌ No face detected. Try a clearer photo.")
                else:
                     status.update(label="Multiple Faces", state="error")
                     st.error("❌ Multiple faces detected.")
                     
            except Exception as e:
                status.update(label="Error", state="error")
                st.error(f"System Error: {e}")

elif choice == "Check In":
    st.subheader("📸 Face Recognition Check-In")
    
    with st.spinner("Loading Face Database..."):
        known_encodings, known_names = load_registered_faces()
    
    if not known_names:
        st.warning("Database empty. Please register or check Debug Info.")
    else:
        st.write(f"Active Users: {len(known_names)}")
        
        # Helper function to process the image bytes
        def process_checkin_image(img_bytes):
            try:
                cv2_img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
                rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
                
                face_locations = face_recognition.face_locations(rgb_img)
                face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
                
                found_match = False
                out_img = cv2_img.copy()

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                    name = "Unknown"

                    if True in matches:
                        first_match_index = matches.index(True)
                        name = known_names[first_match_index]
                        found_match = True
                        success, msg = mark_attendance(name)
                        if success:
                            st.success(msg)
                        else:
                            st.info(msg)

                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(out_img, (left, top), (right, bottom), color, 2)
                    cv2.putText(out_img, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                st.image(out_img, channels="BGR")
                
                if not found_match and len(face_locations) > 0:
                    st.warning("Face detected but not recognized.")
                elif len(face_locations) == 0:
                    st.warning("No face detected in check-in photo.")
            except Exception as e:
                st.error(f"Error processing image: {e}")

        # Tabs for Camera and Upload
        tab1, tab2 = st.tabs(["📸 Camera", "📂 Upload"])
        
        with tab1:
            cam_input = st.camera_input("Check In Camera")
            if cam_input:
                process_checkin_image(cam_input.getvalue())
                
        with tab2:
            up_input = st.file_uploader("Upload Check-In Image", type=['jpg','png','jpeg'])
            if up_input:
                if st.button("Process Check-In"):
                    process_checkin_image(up_input.getvalue())

elif choice == "View Logs":
    st.subheader("📊 Logs")
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            st.dataframe(df)
        except:
            st.info("Empty logs.")
    else:
        st.info("No logs.")
