# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 15:41:25 2023

"""

import os
import shutil
import pydicom
import pprint

# PARAMETERS:
#--------

# enter directory with images to separate
imgdir = r"C:\Users\M305747\OneDrive - Mayo Clinic\MPC\medical-physics\Dr Zhou Projects\Automated Coil QC\GE\ge_HNShead_2023-14-11\IMAGES"

# leave dest_dir as is to get the current folder where .py file is located
# if you want the new folders and images placed there.
dest_dir = os.getcwd()
dest_dir = os.path.join(dest_dir,"organized-imgs")
# otherwise enter a destination folder:
# dest_dir = r"C:\Users\M305747\Desktop\Test\Vida\testingenhanced"
#---------
if dest_dir != "":
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
dcms = [os.path.join(imgdir, x) for x in os.listdir(imgdir)]

contents = []
failed_contents = []
for item in dcms:
        try:
            img = pydicom.dcmread(item)
            seriesInstanceUID = img[0x0020000E].value
            seriesDesc = img[0x0008103E].value or "SeriesDescription"
            imagename=f"{seriesDesc}-{os.path.basename(item)}"
            foldername = f"{seriesDesc}-{seriesInstanceUID}"
            folderpath = os.path.join(dest_dir,foldername)
            
            if not os.path.exists(folderpath):
                os.makedirs(folderpath)
            shutil.copyfile(item,os.path.join(folderpath,imagename))
            
        except:
            print("unknown error with item: {item}")
            failed_contents.append(item)
fail_count = len(failed_contents)
print(f"processed {len(dcms) - fail_count} items successfully")
if len(failed_contents) > 0:
    print(f"Failed {fail_count} items:")
    pprint.pp(failed_contents)
print(f"check destination folder: {dest_dir}")

