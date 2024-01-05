# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 15:41:25 2023

"""

import os
import shutil
import pydicom
import pprint
import tkinter
from tkinter import filedialog
import subprocess

root = tkinter.Tk()
root.wm_attributes('-topmost', 1)
root.withdraw()  # use to hide tkinter window
message = ""

try:
    currdir = os.getcwd()
    tempdir = filedialog.askdirectory(
        parent=root, initialdir=currdir, title="Please select a directory"
    )
    if len(tempdir) > 0:
        print(f"Attempting to process ${tempdir}...")
        srcdir = os.path.abspath(tempdir)
        basedir = os.path.dirname(srcdir)
        foldername = os.path.basename(srcdir)
        dest_dir = os.path.join(basedir,f"{foldername}_organized")
        imgdir = srcdir
       
        # ---------
        if dest_dir != "":
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
    
        dcms = [os.path.join(imgdir, x) for x in os.listdir(imgdir)]
    
        contents = []
        failed_contents = []
        success_contents = []
        message = ""
        folderpath = ""
        for item in dcms:
            try:
                img = pydicom.dcmread(item)
                seriesInstanceUID = img[0x0020000E].value
                seriesDesc = img[0x0008103E].value or "SeriesDescription"
                imagename = f"{seriesDesc}-{os.path.basename(item)}"
                foldername = f"{seriesDesc}-{seriesInstanceUID}"
                folderpath = os.path.join(dest_dir, foldername)
    
                if not os.path.exists(folderpath):
                    os.makedirs(folderpath)
                shutil.copyfile(item, os.path.join(folderpath, imagename))
                success_contents.append(item)
            except:
                failed_contents.append(item)
        fail_count = len(failed_contents)
        success_count = len(success_contents)
        if success_count == 0 and os.path.exists(dest_dir):
            os.rmdir(dest_dir)
            
        if len(failed_contents) > 0:
            message = message + f"Failed to process {fail_count} of {len(dcms)} items: \n"
            for item in failed_contents:
                message = message + f"{item} \n"
        if success_count > 0:
            message = message + f"Finished organizing files, see output folder: {dest_dir}" 
        if len(failed_contents) == 0 and len(success_contents) == len(dcms):
            tkinter.messagebox.showinfo(title="Success", message=message)
        if len(failed_contents) > 0:
            tkinter.messagebox.showwarning(title="Error",message=message)
            os.startfile(dest_dir)
except:
    message = "Something went wrong..."
    tkinter.messagebox.showwarning(title="Error", message=message)