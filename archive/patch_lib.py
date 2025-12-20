path = r"c:/Users/HP/.gemini/antigravity/playground/ancient-ride/Face_recognition/.venv/Lib/site-packages/face_recognition/api.py"

target_block = """try:
    import face_recognition_models
except Exception:
    print("Please install `face_recognition_models` with this command before using `face_recognition`:\\n")
    print("pip install git+https://github.com/ageitgey/face_recognition_models")
    quit()"""

replacement = "import face_recognition_models"

try:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Normalize line endings just in case
    content = content.replace("\\r\\n", "\\n")
    
    if target_block not in content:
        # Try a more loose match if exact string fails (e.g. whitespace diffs)
        print("Exact match not found. Attempting fuzzy match...")
        # Actually, let's just replace the lines 8-13 manually if we know them
        # But dumping showed exact matches.
        pass

    new_content = content.replace(target_block, replacement)
    
    if content == new_content:
        print("WARNING: No replacement made! Check formatting.")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("PATCH SUCCESSFUL: api.py has been modified.")

except Exception as e:
    print(f"Error patching: {e}")
