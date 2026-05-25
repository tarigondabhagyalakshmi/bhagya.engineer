"""
auto_push.py — Auto-commit and push bhagya-website to GitHub
Run this manually, or set up Windows Task Scheduler to run it automatically.

SETUP (one-time):
  1. Replace YOUR_GITHUB_TOKEN below with your GitHub Personal Access Token
     (github.com → Settings → Developer Settings → Personal Access Tokens → Classic → repo scope)
  2. Double-click auto_push.bat to test it, or set up Task Scheduler (see README below).
"""

import subprocess
import sys
import os
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────────────────────────
REPO_DIR    = r"C:\Users\DELL\Documents\Claud-Global\bhagya-website-main"
GITHUB_USER = "nuvvulasainath"
GITHUB_REPO = "bhagya-website"
GITHUB_ORG  = "NARASIMHASAINATHNVL"
GITHUB_TOKEN = "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"   # classic PAT with repo scope
BRANCH      = "main"
# ─────────────────────────────────────────────────────────────────────────────

REMOTE_URL = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_ORG}/{GITHUB_REPO}.git"

def run(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def main():
    os.chdir(REPO_DIR)
    log(f"Working in: {REPO_DIR}")

    # ── 1. Init git if not already a repo ───────────────────────────────────
    code, _, _ = run("git rev-parse --is-inside-work-tree", cwd=REPO_DIR)
    if code != 0:
        log("Initializing git repo...")
        run("git init", cwd=REPO_DIR)
        run(f'git config user.name "Sai"', cwd=REPO_DIR)
        run(f'git config user.email "narasimha.sainath@bankbazaar.com"', cwd=REPO_DIR)
        run(f"git remote add origin {REMOTE_URL}", cwd=REPO_DIR)
        run(f"git fetch origin {BRANCH}", cwd=REPO_DIR)
        run(f"git checkout -b {BRANCH} --track origin/{BRANCH}", cwd=REPO_DIR)
        log("Git repo initialized and connected to GitHub.")
    else:
        # Update remote URL (in case token changed)
        run(f"git remote set-url origin {REMOTE_URL}", cwd=REPO_DIR)

    # ── 2. Pull latest to avoid conflicts ───────────────────────────────────
    log("Pulling latest from GitHub...")
    run(f"git pull origin {BRANCH} --rebase", cwd=REPO_DIR)

    # ── 3. Check for changes ────────────────────────────────────────────────
    code, status, _ = run("git status --porcelain", cwd=REPO_DIR)
    if not status:
        log("✅ No changes to push — everything is up to date.")
        return

    log(f"Changes detected:\n{status}")

    # ── 4. Stage all changes ────────────────────────────────────────────────
    run("git add -A", cwd=REPO_DIR)

    # ── 5. Commit ───────────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"Auto-push: website update [{timestamp}]"
    code, out, err = run(f'git commit -m "{commit_msg}"', cwd=REPO_DIR)
    if code != 0:
        log(f"Commit failed: {err}")
        sys.exit(1)
    log(f"Committed: {commit_msg}")

    # ── 6. Push ─────────────────────────────────────────────────────────────
    log(f"Pushing to GitHub ({BRANCH})...")
    code, out, err = run(f"git push origin {BRANCH}", cwd=REPO_DIR)
    if code != 0:
        log(f"❌ Push failed: {err}")
        sys.exit(1)

    log("🚀 Successfully pushed to GitHub! Vercel will deploy in ~30 seconds.")
    log(f"   Live at: https://bhagya.engineer")

if __name__ == "__main__":
    main()
