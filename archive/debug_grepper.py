import os

root_dir = r"c:/Users/HP/.gemini/antigravity/playground/ancient-ride/Face_recognition/.venv/Lib/site-packages/face_recognition"
search_str = "Please install"

print(f"Searching in {root_dir}...")

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if search_str in content:
                        print(f"FOUND IN: {path}")
                        print("CONTENT START ============")
                        print(content)
                        print("CONTENT END ==============")
            except Exception as e:
                print(f"Could not read {path}: {e}")
