#!/usr/bin/env python3
"""
push_to_github.py — Push pending blog files to bhagya.engineer GitHub repo
----------------------------------------------------------------------
HOW TO RUN:
  1. Open Command Prompt or PowerShell in this folder
  2. python push_to_github.py
  3. Paste your GitHub PAT when prompted

HOW TO GET A GITHUB PAT (takes 30 seconds):
  GitHub.com → Settings → Developer Settings
  → Personal Access Tokens → Fine-grained tokens → Generate new token
  → Repository: NARASIMHASAINATHNVL/bhagya-website
  → Permissions: Contents → Read and Write
  → Generate token → Copy it
"""
import base64, os, sys

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip install requests")
    import requests

REPO   = "NARASIMHASAINATHNVL/bhagya-website"
BASE   = "https://api.github.com"
BRANCH = "main"
HERE   = os.path.dirname(os.path.abspath(__file__))

FILES = [
    (
        "blog/admin.html",
        os.path.join(HERE, "blog", "admin.html"),
        "feat: add blog/admin.html — protected dashboard with Quill editor"
    ),
    (
        "blog/posts.json",
        os.path.join(HERE, "blog", "posts.json"),
        "fix: update blog/posts.json — full article content"
    ),
]

def push_file(token, gh_path, local_path, commit_msg):
    headers = {
        "Authorization": f"token {token}",
        "Accept":        "application/vnd.github.v3+json",
        "Content-Type":  "application/json",
    }
    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    get_r = requests.get(f"{BASE}/repos/{REPO}/contents/{gh_path}", headers=headers)
    body  = {"message": commit_msg, "content": content_b64, "branch": BRANCH}
    if get_r.status_code == 200:
        body["sha"] = get_r.json()["sha"]
        action = "Updated"
    else:
        action = "Created"

    put_r = requests.put(
        f"{BASE}/repos/{REPO}/contents/{gh_path}",
        headers=headers, json=body
    )
    if put_r.status_code in (200, 201):
        print(f"  [OK] {action}: {gh_path}  (HTTP {put_r.status_code})")
        return True
    else:
        print(f"  [FAIL] {gh_path}  (HTTP {put_r.status_code})")
        print(f"         {put_r.text[:300]}")
        return False


def main():
    print()
    print("=" * 55)
    print("  bhagya.engineer — GitHub Push Script")
    print("=" * 55)
    print()

    import getpass
    token = getpass.getpass("Paste your GitHub PAT (input hidden): ").strip()
    if not token:
        print("No token entered. Exiting.")
        sys.exit(1)

    # Verify token
    me = requests.get(f"{BASE}/user", headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    })
    if me.status_code != 200:
        print(f"[ERROR] Token invalid or no API access (HTTP {me.status_code})")
        sys.exit(1)
    print(f"Authenticated as: {me.json().get('login', '?')}")
    print()

    success = 0
    for gh_path, local_path, msg in FILES:
        if not os.path.exists(local_path):
            print(f"  [SKIP] Not found locally: {local_path}")
            continue
        size_kb = os.path.getsize(local_path) / 1024
        print(f"Pushing {gh_path} ({size_kb:.1f} KB) ...")
        if push_file(token, gh_path, local_path, msg):
            success += 1

    print()
    print(f"Result: {success}/{len(FILES)} files pushed to GitHub.")
    if success > 0:
        print()
        print("Vercel will auto-deploy in ~30 seconds.")
        print()
        print("Live URLs once deployed:")
        print("  Blog front:  https://bhagya.engineer/blog/")
        print("  Admin panel: https://bhagya.engineer/blog/admin.html")
        print("  Sample post: https://bhagya.engineer/blog/post.html?id=technical-seo-errors-fintech")

    print()
    input("Press Enter to close...")


if __name__ == "__main__":
    main()
