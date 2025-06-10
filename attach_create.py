# Aliza Lazar – 336392899
# Raz Cohen – 208008995

import os
import shutil
from PyInstaller.__main__ import run  # Directly import the 'run' function from PyInstaller to build the executable

def create_exe():
    # If the 'dist' directory (default PyInstaller output dir) exists from a previous run, delete it
    if os.path.exists("dist"):
        shutil.rmtree("dist")

    # If the 'build' directory exists, delete it
    if os.path.exists("build"):
        shutil.rmtree("build")

    # If an old version of the output file 'attachment' exists in the current directory, delete it
    if os.path.exists("attachment"):
        os.remove("attachment")

    # Build Phase (Create Executable)

    # Run PyInstaller to convert the Python script 'attachment_payload.py' into a single-file executable
    run([
        "attachment_payload.py", #This is the script we want to convert into an executable
        "--onefile", #Package everything into one .exe (no folders or dependencies)
        "--distpath", ".", #Output the final executable in the current directory
        "--name", "attachment" #Name of the output file 'attachment'
    ])

    # Inform the user that the executable was successfully created
    print("\n[+] Executable 'attachment' created successfully.")


# This ensures that 'create_exe()' only runs when this script is executed directly (not imported)
if __name__ == "__main__":
    create_exe()
