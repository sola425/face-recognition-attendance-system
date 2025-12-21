# Deployment Guide: Existing GitHub Repo to Hugging Face

Since you already have a repository, updating is easy.

## 1. Clean Up & Prepare
*   **Kept:** `main.py` (Local), `app.py` (Online), `Dockerfile`, `requirements.txt`.
*   **Allowed:** `Strangers/` (Now included in upload).
*   **Ignored:** `archive/` (Backup), `.venv/`.

## 2. Push Changes to GitHub
Open your terminal in the project folder and run:

```bash
# 1. Check what changed
git status

# 2. Add the new deployment files (Dockerfile, requirements.txt, .dockerignore)
git add .

# 3. Save your snapshot
git commit -m "Add Docker deployment configuration"

# 4. Push to your existing repository
git push
```

## 3. Connect to Hugging Face
1.  Go to your **Hugging Face Space**.
2.  Click **Settings** (top right).
3.  Scroll to **"Docker"** or **"Repository"** section.
4.  Look for **"Link to GitHub"** or "Connect Repository".
5.  Authorize GitHub and select your repo.
6.  It will start building automatically!
