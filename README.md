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

A robust, real-time Facial Recognition system built with Python, OpenCV, and Streamlit. This project includes both a **Desktop Agent** (with Liveness Detection) and a **Web Application** (deployable to Streamlit Cloud).

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

### 3. 📝 Instant User Registration
- New users can register themselves directly on the web app.
- Simply enter a name and take a selfie.
- The system immediately "learns" the new face without restarting.

### 4. 🕵️ Stranger Alert
- If an unknown person is detected, they are marked as "STRANGER".
- Their photo is automatically captured and saved to the `Strangers/` folder for security review.

## ⚠️ Important Limitations

### Cloud Deployment (Streamlit Cloud)
- **Slow Build Time**: First deployment can take 15+ minutes due to compiling `dlib`. This is normal.
- **Ephemeral Storage**: All registered users are DELETED if the app restarts. (Use local version for permanent storage).
- **Performance**: Real-time video may lag depending on user internet speed. The "Desktop Agent" (`main.py`) is recommended for critical real-time checkpoints.

### Desktop Agent (`main.py`)
- **Full Power**: No lag, permanent storage, robust liveness detection.
- **Requirement**: Must be run on a computer with a webcam.

---

## 🛠️ Architecture

```mermaid
graph TD
    A[User] -->|Interacts with| B[Streamlit Web App]
    A -->|Interacts with| C[Desktop App (main.py)]
    
    subgraph Web App (app.py)
        B1[Register Mode]
        B2[Check-In Mode]
        B --> B1
        B --> B2
        B1 -->|Saves Photo| D[Images_Attendance Folder]
        B2 -->|Reads Photos| D
        B2 -->|Writes Log| E[Attendance.csv]
    end

    subgraph Desktop App (main.py)
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
2.  Run: `pip install dlib-19.24.99-cp313-cp313-win_amd64.whl`
3.  Run: `pip install -r requirements.txt`

**For Streamlit Cloud (Auto-Build):**
- You do NOT need the wheel file.
- The `packages.txt` file (included) tells the Cloud server to install `cmake`.
- The Cloud will automatically compile `dlib` from source. **Note:** This takes 10-15 minutes ("in the oven") to build the first time.

### 2. Run the Web App
```bash
streamlit run app.py
```

### 3. Run the Desktop Agent (Optional)
```bash
python main.py
```

---

## ☁️ Deployment Guide (Streamlit Cloud)

Since this app uses `dlib`, deployment requires a specific setup.

1. **GitHub**: Push this code to a public GitHub repository.
2. **Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io).
   - Click "New App".
   - Select your repository and the main file `app.py`.
3. **Advanced Settings (packages.txt)**:
   - Ensure you have a `packages.txt` file in your repo containing:
     ```
     cmake
     libx11-dev
     ```
   - This ensures the Linux server can compile the face recognition libraries.

> **⚠️ NOTE: Ephemeral Storage**
> Streamlit Cloud does not have a permanent hard drive. If you register a user, their photo will be **deleted** if the app restarts or goes to sleep.
> *To fix this for production, you would need to connect the app to an AWS S3 bucket or Google Drive.*

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

## 📸 Screenshots

| Registration Page | Liveness Check |
|:---:|:---:|
| *(Place screenshot here)* | *(Place screenshot here)* |

| CSV Data View | Stranger Alert |
|:---:|:---:|
| *(Place screenshot here)* | *(Place screenshot here)* |

---

## 🤝 Contributing
Feel free to fork this project and submit Pull Requests.

````
# 📸 Face Recognition Attendance System

A robust, real-time Facial Recognition system built with Python, OpenCV, and Streamlit. This project includes both a **Desktop Agent** (with Liveness Detection) and a **Web Application** (deployable to Streamlit Cloud).

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

### 3. 📝 Instant User Registration
- New users can register themselves directly on the web app.
- Simply enter a name and take a selfie.
- The system immediately "learns" the new face without restarting.

### 4. 🕵️ Stranger Alert
- If an unknown person is detected, they are marked as "STRANGER".
- Their photo is automatically captured and saved to the `Strangers/` folder for security review.

## ⚠️ Important Limitations

### Cloud Deployment (Streamlit Cloud)
- **Slow Build Time**: First deployment can take 15+ minutes due to compiling `dlib`. This is normal.
- **Ephemeral Storage**: All registered users are DELETED if the app restarts. (Use local version for permanent storage).
- **Performance**: Real-time video may lag depending on user internet speed. The "Desktop Agent" (`main.py`) is recommended for critical real-time checkpoints.

### Desktop Agent (`main.py`)
- **Full Power**: No lag, permanent storage, robust liveness detection.
- **Requirement**: Must be run on a computer with a webcam.

---

## 🛠️ Architecture

```mermaid
graph TD
    A[User] -->|Interacts with| B[Streamlit Web App]
    A -->|Interacts with| C[Desktop App (main.py)]
    
    subgraph Web App (app.py)
        B1[Register Mode]
        B2[Check-In Mode]
        B --> B1
        B --> B2
        B1 -->|Saves Photo| D[Images_Attendance Folder]
        B2 -->|Reads Photos| D
        B2 -->|Writes Log| E[Attendance.csv]
    end

    subgraph Desktop App (main.py)
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
2.  Run: `pip install dlib-19.24.99-cp313-cp313-win_amd64.whl`
3.  Run: `pip install -r requirements.txt`

**For Streamlit Cloud (Auto-Build):**
- You do NOT need the wheel file.
- The `packages.txt` file (included) tells the Cloud server to install `cmake`.
- The Cloud will automatically compile `dlib` from source. **Note:** This takes 10-15 minutes ("in the oven") to build the first time.

### 2. Run the Web App
```bash
streamlit run app.py
```

### 3. Run the Desktop Agent (Optional)
```bash
python main.py
```

---

## ☁️ Deployment Guide (Streamlit Cloud)

Since this app uses `dlib`, deployment requires a specific setup.

1. **GitHub**: Push this code to a public GitHub repository.
2. **Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io).
   - Click "New App".
   - Select your repository and the main file `app.py`.
3. **Advanced Settings (packages.txt)**:
   - Ensure you have a `packages.txt` file in your repo containing:
     ```
     cmake
     libx11-dev
     ```
   - This ensures the Linux server can compile the face recognition libraries.

> **⚠️ NOTE: Ephemeral Storage**
> Streamlit Cloud does not have a permanent hard drive. If you register a user, their photo will be **deleted** if the app restarts or goes to sleep.
> *To fix this for production, you would need to connect the app to an AWS S3 bucket or Google Drive.*

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

## 📸 Screenshots

| Registration Page | Liveness Check |
|:---:|:---:|
| *(Place screenshot here)* | *(Place screenshot here)* |

| CSV Data View | Stranger Alert |
|:---:|:---:|
| *(Place screenshot here)* | *(Place screenshot here)* |

---

## 🤝 Contributing
Feel free to fork this project and submit Pull Requests.
