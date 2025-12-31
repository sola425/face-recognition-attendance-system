# Base Image: Miniforge3 (Uses Mamba - Faster & More Stable than Conda)
FROM condaforge/miniforge3

# 1. Install System Libraries (Required for OpenCV)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Heavy AI Libraries via Mamba (Solves specific "Segfault" error)
RUN mamba install -y -c conda-forge \
    python=3.9 \
    dlib \
    face_recognition \
    numpy \
    opencv \
    && mamba clean -afy

# 3. Install Web UI Libraries via Pip
RUN pip install --no-cache-dir \
    streamlit \
    streamlit-webrtc \
    av \
    setuptools \
    pandas

# 4. Set Up Application
WORKDIR /app
COPY . .

# 5. Security: Run as non-root user (Required by Hugging Face)
# Handle potential pre-existing user 1000
RUN useradd -m -u 1000 user || true
RUN chown -R 1000:1000 /app
USER 1000
ENV HOME=/app
ENV PATH="/home/user/.local/bin:$PATH"

# 6. Launch
CMD ["streamlit", "run", "app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]

