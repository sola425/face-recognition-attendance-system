import streamlit as st
import face_recognition
import cv2
import numpy as np
import os
import pandas as pd
from datetime import datetime

# ==========================================
# 1. Setup & Config
# ==========================================
st.set_page_config(page_title="Easy Attendance System", layout="wide")

PATH_IMAGES = 'Images_Attendance'
FILE_DB = 'Attendance.csv'

if not os.path.exists(PATH_IMAGES):
    os.makedirs(PATH_IMAGES)

# Ensure CSV exists with headers
if not os.path.exists(FILE_DB):
    df = pd.DataFrame(columns=['Name', 'Time', 'Date'])
    df.to_csv(FILE_DB, index=False)

# ==========================================
# 2. Optimized Helper Functions
# ==========================================

@st.cache_resource
def get_known_faces():
    """
    Load images once and cache them. 
    Returns: known_encodings, known_names
    """
    encodings = []
    names = []
    
    # scan folder
    files = [f for f in os.listdir(PATH_IMAGES) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    if not files:
        return [], []

    # Optional: Logic to show loading progress
    # on first load, this might take a moment
    
    for file in files:
        try:
            img_path = os.path.join(PATH_IMAGES, file)
            img = cv2.imread(img_path)
            if img is None:
                continue
                
            # Resize if too big (limit width to 800px)
            height, width = img.shape[:2]
            if width > 800:
                scale = 800 / width
                img = cv2.resize(img, (0, 0), fx=scale, fy=scale)
            
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = face_recognition.face_encodings(img_rgb)
            
            # Rotation checks if no face found initially
            if not results:
                # 90 clockwise
                img_cw = cv2.rotate(img_rgb, cv2.ROTATE_90_CLOCKWISE)
                results = face_recognition.face_encodings(img_cw)
            
            if not results:
                # 270 (90 ccw)
                img_ccw = cv2.rotate(img_rgb, cv2.ROTATE_90_COUNTERCLOCKWISE)
                results = face_recognition.face_encodings(img_ccw)

            if results:
                encodings.append(results[0])
                names.append(os.path.splitext(file)[0].replace('_', ' '))
                
        except Exception as e:
            print(f"Error loading {file}: {e}")
            
    return encodings, names

def mark_in_csv(name):
    """
    Uses Pandas to check and log attendance.
    """
    try:
        if not os.path.exists(FILE_DB):
             df = pd.DataFrame(columns=['Name', 'Time', 'Date'])
        else:
             df = pd.read_csv(FILE_DB)
             
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        # Check if name exists for today's date
        if df.empty:
             is_marked = False
        else:
             is_marked = ((df['Name'] == name) & (df['Date'] == date_str)).any()

        if not is_marked:
            new_entry = pd.DataFrame({'Name': [name], 'Time': [time_str], 'Date': [date_str]})
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(FILE_DB, index=False)
            return "Marked ✅"
        return "Already Checked In ⚠️"
    except Exception as e:
        return f"Error: {str(e)}"

# ==========================================
# 3. Main App UI
# ==========================================

st.title("📍 Easy Attendance System")
menu = ["Check In", "Register User", "View Log"]
choice = st.sidebar.selectbox("Menu", menu)

# --- REGISTER USER ---
if choice == "Register User":
    st.subheader("Register New Face")
    name = st.text_input("Enter Name:")
    picture = st.camera_input("Take a clear selfie")
    
    if st.button("Save Profile"):
        if name and picture:
            bytes_data = picture.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            
            filename = f"{name.replace(' ', '_')}.jpg"
            cv2.imwrite(os.path.join(PATH_IMAGES, filename), cv2_img)
            
            st.success(f"Registered {name} successfully!")
            st.cache_resource.clear()
        else:
            st.error("Please provide both a name and a photo.")

# --- CHECK IN ---
elif choice == "Check In":
    st.subheader("Mark Attendance")
    
    with st.spinner("Loading face database..."):
        known_enc, known_names = get_known_faces()
        
    if not known_names:
        st.warning("No users registered yet. Please register first.")
    
    st.write(f"**System Ready**: {len(known_names)} users in database.")

    # TABS instead of Radio for better UI
    tab1, tab2 = st.tabs(["📸 Take Snapshot", "📂 Upload Photo"])

    img_input = None

    # Tab 1: Snapshot
    with tab1:
        st.info("Use your camera to take a snapshot.")
        snapshot = st.camera_input("Take Snapshot", key="snapshot_cam")
        if snapshot:
            img_input = snapshot

    # Tab 2: Upload
    with tab2:
        st.info("Upload an image file (JPG, PNG).")
        uploaded = st.file_uploader("Choose a file", type=['jpg', 'jpeg', 'png'], key="upload_cam")
        if uploaded:
            img_input = uploaded

    # Common Processing Block
    if img_input is not None:
        st.write("---")
        # Explicit button to process (prevents auto-run and glitching)
        if st.button("🔍 Identify & Mark Attendance", type="primary"):
            
            with st.spinner("Processing image..."):
                try:
                    # 1. Read Image
                    bytes_data = img_input.getvalue()
                    img_bgr = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                    
                    if img_bgr is None:
                        st.error("Error reading image data.")
                        st.stop()
                    
                    # 2. Resize for Speed (Max 800px width)
                    height, width = img_bgr.shape[:2]
                    if width > 800:
                        scale = 800 / width
                        img_bgr = cv2.resize(img_bgr, (0, 0), fx=scale, fy=scale)

                    # 3. Convert to RGB
                    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                    
                    # 4. Detect Faces
                    face_locs = face_recognition.face_locations(img_rgb)
                    face_encs = face_recognition.face_encodings(img_rgb, face_locs)

                    # 5. Draw on Image
                    # We work on img_bgr for drawing, then convert back to RGB for display
                    # Or just draw on a copy of RGB
                    img_display = img_rgb.copy()

                    if not face_encs:
                        st.warning("No faces detected! Please try again with a clearer photo.")
                    else:
                        st.success(f"Detected {len(face_encs)} face(s). Checking database...")
                        
                        count_identified = 0
                        
                        for enc, loc in zip(face_encs, face_locs):
                            # Compare
                            face_dist = face_recognition.face_distance(known_enc, enc)
                            match_index = np.argmin(face_dist)
                            min_dist = face_dist[match_index]
                            
                            # Threshold check
                            if min_dist < 0.6:
                                name = known_names[match_index]
                                # Mark Attendance
                                status = mark_in_csv(name)
                                
                                # Draw Box Green
                                top, right, bottom, left = loc
                                cv2.rectangle(img_display, (left, top), (right, bottom), (0, 255, 0), 2)
                                
                                # Label
                                cv2.rectangle(img_display, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                                cv2.putText(img_display, name, (left + 6, bottom - 6), 
                                            cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
                                
                                st.success(f"✅ **{name}** - {status}")
                                count_identified += 1
                            else:
                                # Unknown
                                top, right, bottom, left = loc
                                cv2.rectangle(img_display, (left, top), (right, bottom), (0, 0, 255), 2)
                                cv2.putText(img_display, "Unknown", (left, bottom + 25), 
                                            cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 1)
                        
                        if count_identified == 0:
                            st.error("No registered users recognized.")
                            
                    # Display Final Image with Boxes
                    st.image(img_display, caption="Processed Result", use_column_width=True)

                except Exception as e:
                    st.error(f"Error during processing: {e}")

# --- VIEW LOG ---
elif choice == "View Log":
    st.subheader("Attendance Records")
    if os.path.exists(FILE_DB):
        df = pd.read_csv(FILE_DB)
        st.dataframe(df.style.highlight_max(axis=0)) # simple style
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "attendance.csv", "text/csv")
    else:
        st.info("No records found.")
