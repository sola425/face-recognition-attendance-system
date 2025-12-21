# Base Image: Miniconda (Pre-configured with Conda package manager)
FROM continuumio/miniconda3

# 1. Install System Libraries (Required for OpenCV/Use of Camera)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Heavy AI Libraries via Conda (Fast & Pre-compiled)
# This installs dlib, face_recognition, and numpy binaries in seconds.
RUN conda install -y -c conda-forge \
    dlib \
    face_recognition \
    numpy \
    opencv

# 3. Install Web UI Libraries via Pip
# We list them here directly to avoid conflicts with local requirements.txt
RUN pip install --no-cache-dir \
    streamlit \
    streamlit-webrtc \
    av \
    setuptools

# 4. Set Up Application
WORKDIR /app
COPY . .

# 5. Security: Run as non-root user (Required by Hugging Face)
RUN useradd -m -u 1000 user
RUN chown -R user:user /app
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# 6. Launch
CMD ["streamlit", "run", "app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]

