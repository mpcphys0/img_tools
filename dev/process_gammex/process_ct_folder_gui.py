import sys
import os
import tkinter
from tkinter import filedialog
import tkinter.ttk as ttk

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


def run_process():
    try:
        tempdir = filedialog.askdirectory(
            parent=root, initialdir=currentdir, title="Please select a directory"
        )
        if tempdir == "":
            print("Process cancelled...")
            return None
        imagedir_path = os.path.abspath(tempdir)
        reportdir_path = os.path.join(
            os.path.dirname(imagedir_path),
            f"{os.path.basename(imagedir_path)}_report",
        )
        ctfunctions.process_single_series_folder(imagedir_path, reportdir_path)
        message = f"finished processing phantom images. \nPlease check {reportdir_path} for results."
        tkinter.messagebox.showinfo(title="Finished", message=message)
        print(
            f"finished processing phantom images. \nPlease check {reportdir_path}\nfor results."
        )
    except:
        message = f"Something went wrong. Results may be invalid or incomplete. \nPlease check reports folder: {reportdir_path}"
        tkinter.messagebox.showerror(title="Error", message=message)
        print("something went wrong...")


run_process()
