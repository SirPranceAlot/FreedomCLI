import os
import shutil
import subprocess
import sys

def clean():
    """Remove build artifacts."""
    dirs_to_remove = ["dist", "build", "orchat.egg-info"]
    for path in dirs_to_remove:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"Removed {path}")

def build():
    """Build the package using the 'build' module."""
    try:
        import build
    except ImportError:
        print("Installing build tool...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "build"])
    
    clean()
    print("Building package...")
    subprocess.check_call([sys.executable, "-m", "build"])

if __name__ == "__main__":
    try:
        build()
        print("\nBuild successful! Artifacts are in 'dist/' directory.")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)
