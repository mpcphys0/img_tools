import sys
import os
import tkinter
from tkinter import filedialog

print("initializing ct functions...")

# add path for importing ctfunctions.py
currentdir = os.getcwd()
ctfunctions_path = currentdir
sys.path.insert(1, ctfunctions_path)

# import and test ctfunctions.py
import ctfunctions

try:
    ctfunctions.test_print()
except:
    print(
        "Error loading ctfunctions.py... Please ensure process_phantom.py and ct_functions.py are located in the same directory."
    )

root = tkinter.Tk()
root.wm_attributes("-topmost", 1)
root.withdraw()  # use to hide tkinter window
message = ""

try:
    tempdir = filedialog.askdirectory(
        parent=root, initialdir=currentdir, title="Please select a directory"
    )
    imagedir_path = os.path.abspath(tempdir)
    reportdir_path = os.path.join(
        os.path.dirname(imagedir_path),
        f"{os.path.basename(imagedir_path)}_report",
    )

    ctfunctions.process_single_series_folder(imagedir_path, reportdir_path)
except:
    print("something went wrong...")
