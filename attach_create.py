# Aliza Lazar – 336392899
# Raz Cohen – 208008995
import os
import shutil
from PyInstaller.__main__ import run

def create_exe():
    # Clean up previous build artifacts
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("attachment"):
        os.remove("attachment")

    # Run PyInstaller to create a standalone executable
    run([
        "attachment_payload.py",  # Source script to compile
        "--onefile",              # Create a single-file executable
        "--distpath", ".",        # Output to current directory
        "--name", "attachment"    # Output file name
    ])

    print("\n[+] Executable 'attachment' created successfully.")

if __name__ == "__main__":
    create_exe()