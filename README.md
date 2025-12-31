---
title: Face Recognition Attendance System
emoji: 📸
colorFrom: blue
colorTo: indigo
sdk: docker
sdk_version: 1.35.0
app_file: app.py
pinned: false
license: mit
---

# 📸 Face Recognition Attendance System

**🚀 Live Demo**: [Click here to access the Deployed App on Hugging Face](https://sola425-facial-recognition-attendance-v2.hf.space)

A robust, real-time Facial Recognition system built with Python, OpenCV, and Streamlit. This project includes both a **Desktop Agent** (with Liveness Detection) and a **Web Application** (deployed on Hugging Face Spaces).

![Banner Placeholder](https://via.placeholder.com/1000x200?text=Face+Recognition+Attendance+System)

## 🌟 Key Features

### 1. 📍 Live Attendance Tracking
- Automatically recognizes registered users.
- Logs attendance to a CSV file (`Attendance.csv`) with Time and Date.
- Prevents double-marking (users can only check in once per day).

### 2. 🛡️ Liveness Detection (Anti-Spoofing)
- **Problem**: Someone could hold up a photo of you to fake your attendance.
- **Solution**: The system tracks eye blinks. Attendance is only marked if the user blinks properly, proving they are a real person.
- *Available in: Advanced Mode / Desktop App*

![Liveness Check](assets/liveness_check_screenshot.png)

### 3. 📝 Instant User Registration
- New users can register themselves directly on the web app.
- Simply enter a name and take a selfie.
- The system immediately "learns" the new face without restarting.

![Registration Page](assets/registration_screenshot.png)

### 4. 🕵️ Stranger Alert
- If an unknown person is detected, they are marked as "STRANGER".
- Their photo is automatically captured and saved to the `Strangers/` folder for security review.

![Stranger Alert](assets/stranger_alert_screenshot.png)

---

## 🧠 Beginner's Guide: Understanding the Code

Here is a simplified explanation of how the system works, designed for beginners.

### 🐍 `main.py` (The Brain of the Operation)
This script runs on your **local computer**. It controls the webcam and does the heavy lifting.

1.  **Imports Libraries**: We load tools like `cv2` (OpenCV) for vision and `face_recognition` for AI.
2.  **Setup Folders**: The code checks if `Images_Attendance` and `Strangers` folders exist. If not, it creates them.
3.  **Encodes Known Faces**: 
    - At startup, the system loops through every photo in `Images_Attendance`.
    - It learns the unique "face map" (encoding) of each person and stores it in memory (`known_face_encodings`).
4.  **Opens Webcam**: `cv2.VideoCapture(0)` turns on your camera.
5.  **The Infinite Loop (`while True`)**:
    - **Read Frame**: It grabs a single picture from the video stream.
    - **Face Detection**: It looks for faces giving coordinates (Top, Right, Bottom, Left).
    - **Matching**: It compares the detected face against the memory of "Known Faces".
    - **Liveness Check**: It measures the "Eye Aspect Ratio" (EAR). If your eyes close (blink) and open again, it marks you as `LIVNESS_VERIFIED`.
    - **Attendance**: If (Face Matches AND Liveness Verified), it writes your name and time to `Attendance.csv`.
    - **Stranger Alert**: If no match is found, it draws a red box and saves the intruder's photo.

### 🌐 `app.py` (The Web Interface)
This script runs in the **Browser** (via Streamlit). It's user-friendly and great for registration.

1.  **Sidebar Menu**: Allows you to switch between "Check In", "Register New User", and "View Logs".
2.  **Registration Mode**:
    - You type a name and take a photo.
    - The app saves the photo as `Name.jpg` in the `Images_Attendance` folder.
    - *Magic*: This file is automatically picked up by `main.py` next time it runs!
3.  **Check-In Mode**:
    - Works similarly to `main.py` but processes single images (uploaded or snapped) instead of a video stream.
4.  **View Logs**: Reads `Attendance.csv` using `pandas` and displays it as a neat table.

---

## ⚠️ Deployment Notes (Why Hugging Face?)

We deployed this application on **Hugging Face Spaces** instead of Streamlit Cloud for one critical reason: **Memory (RAM)**.

- **The Challenge**: The `face_recognition` library requires compiling `dlib`, which is a very heavy C++ library. During installation, it consumes a large amount of RAM.
- **The Issue**: Streamlit Cloud's free tier has a strict memory limit. When it tries to install `dlib`, it often crashes ("Out of Memory").
- **The Solution**: Hugging Face Spaces (using Docker) provides a more robust environment that handles the heavy installation process smoothly.

**Live Link**: [https://sola425-facial-recognition-attendance-v2.hf.space](https://sola425-facial-recognition-attendance-v2.hf.space)

---

## 🛠️ Architecture

```mermaid
graph TD
    A[User] -->|Interacts with| B["Hugging Face Space (Running app.py)"]
    A -->|Interacts with| C["Desktop App (main.py)"]
    
    subgraph "Cloud Deployment (Hugging Face)"
        B1[Register Mode]
        B2[Check-In Mode]
        B --> B1
        B --> B2
        B1 -->|Saves Photo| D[Images_Attendance Folder]
        B2 -->|Reads Photos| D
        B2 -->|Writes Log| E[Attendance.csv]
    end

    subgraph "Local Machine (Desktop)"
        C -->|Reads Photos| D
        C -->|Writes Log| E
        C -->|Saves Strangers| F[Strangers Folder]
        C1[Liveness Logic]
        C --> C1
    end
```

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.8+
- CMake (Required for `dlib`)
- Visual Studio Build Tools (Windows only, for `dlib`)

### 1. Clone & Install
**For Local Windows Users (Fastest):**
1.  Download the `dlib` wheel file (provided in repo).
2.  Run: `pip install dlib-19.24.99-cp313-cp313-win_amd64.whl` (or appropriate version)
3.  Run: `pip install -r requirements.txt`

### 2. Run the Web App
```bash
streamlit run app.py
```

### 3. Run the Desktop Agent (Optional)
```bash
python main.py
```

---

## 📂 Project Structure

- `main.py`: The robust desktop script with OpenCV windows.
- `app.py`: The modern web interface using Streamlit.
- `Images_Attendance/`: Database of known faces.
- `Strangers/`: Security logs of unknown people.
- `Attendance.csv`: The daily log file.
- `requirements.txt`: Python dependencies.
- `packages.txt`: System dependencies for Linux deployment.

---

## 🤝 Contributing
Feel free to fork this project and submit Pull Requests.

