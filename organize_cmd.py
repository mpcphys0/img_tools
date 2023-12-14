# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 14:06:16 2023

Command line tool to take a set of dicom files and separate them
into folders based on their series UID and also add the series
description if present to the folder name and filename of each 
dicom file

"""
import os
import sys
import argparse
import pydicom
import pprint
import shutil

parser = argparse.ArgumentParser(
    description="Separate and name DICOM files by series UID", 
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
parser.add_argument("src",help="source folder where dicom files/folders are located")
parser.add_argument("dest", help="destination folder to save newly organized image folders")
args = parser.parse_args()

config = vars(args)
imgdir = config["src"]
dest_dir = config["dest"]

# list all files down the folder tree
files = [
    os.path.join(dirpath, f)
    for (dirpath, dirnames, filenames) in os.walk(
        imgdir
    )
    for f in filenames
]

# files = [os.path.join(imgdir, x) for x in os.listdir(imgdir)]

contents = []
failed_contents = []
for item in files:
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
            print(f"unknown error with item: {item}")
            failed_contents.append(item)
fail_count = len(failed_contents)
print(f"processed {len(files) - fail_count} items successfully")
if len(failed_contents) > 0:
    print(f"Failed {fail_count} items:")
    pprint.pp(failed_contents)
print(f"check destination folder: {dest_dir}")