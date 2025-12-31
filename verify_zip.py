
import shutil
import os

# Simulate REPO_ROOT detection (Local fallback)
if os.path.exists("./src"):
    REPO_ROOT = os.path.abspath(".")
    print(f"REPO_ROOT: {REPO_ROOT}")
else:
    print("Error: Local src not found")
    exit(1)

try:
    src_path = os.path.join(REPO_ROOT, 'src')
    
    if os.path.exists(src_path):
        print(f"Zipping src folder from: {src_path}...")
        # Create zip in current directory
        shutil.make_archive("submission_src", "zip", root_dir=REPO_ROOT, base_dir="src")
        print("✓ submission_src.zip created successfully")
    else:
        print(f"❌ Error: src folder not found at {src_path}")
        
except Exception as e:
    print(f"❌ Failed to create submission zip: {e}")

if os.path.exists("submission_src.zip"):
    print("✓ All Checks Passed")
    # clean up
    os.remove("submission_src.zip")
