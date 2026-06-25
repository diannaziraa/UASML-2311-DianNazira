#!/usr/bin/env python
"""
Backend startup script - cepat!
Langsung run FastAPI, install packages jika diperlukan
"""
import subprocess
import sys
import os

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn[standard]",
    "python-multipart",
    "Pillow",
    "google-genai",
    "google-api-core",
    "python-dotenv",
    "numpy",
    "tensorflow",
]

def check_and_install():
    """Check dan install dependencies jika kurang"""
    print("🔍 Checking dependencies...")
    missing = []
    
    for pkg in REQUIRED_PACKAGES:
        pkg_name = pkg.split("[")[0].replace("-", "_").replace(".", "_")
        try:
            __import__(pkg_name)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"⬇ Installing {len(missing)} missing packages...")
        for pkg in missing:
            print(f"  📦 {pkg}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])
            except:
                print(f"  ⚠️ Failed to install {pkg}, continuing...")
    
    print("✅ All core packages ready!\n")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        check_and_install()
    except Exception as e:
        print(f"Warning during dependency check: {e}")
    
    print("🚀 Starting FastAPI server...")
    print("📍 http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs\n")
    
    os.execvp(sys.executable, [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])

