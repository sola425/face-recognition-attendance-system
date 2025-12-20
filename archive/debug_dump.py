path = r"c:/Users/HP/.gemini/antigravity/playground/ancient-ride/Face_recognition/.venv/Lib/site-packages/face_recognition/api.py"
try:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    with open("library_dump.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("Dump successful")
except Exception as e:
    print(f"Error: {e}")
