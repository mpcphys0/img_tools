import pydicom
import pandas as pd
import os
from datetime import datetime
import tkinter
from tkinter import filedialog
import subprocess

def openloc(path):
    os.start(path,"open")

root = tkinter.Tk()
root.wm_attributes('-topmost', 1)
root.withdraw()  # hide tkinter root window
message = ""

currdir = os.getcwd()
tempdir = filedialog.askopenfilenames(
    parent=root, initialdir=currdir, title="Please select two DICOM image files"
)

# try:
if len(tempdir) != 2:
    message = "Please select exactly 2 image files..."
    tkinter.messagebox.showerror(title="Error", message=message)

if len(tempdir) == 2:
    
    #set path of image1 and image2 to be compared
    path1 = tempdir[0]
    path2 = tempdir[1]
    filename1 = os.path.basename(path1)
    filename2 = os.path.basename(path2)
    # use current working directory for output files, change if needed.
    #destpath = os.getcwd()
    
    destpath = os.path.dirname(path1)
    
    #generate timestamp for filename
    now = datetime.now()
    timestamp = now.strftime("%m%d%y_%H%M%S")
    
    #read image with pydicom
    img1 = pydicom.dcmread(path1)
    img2 = pydicom.dcmread(path2)
    list1 = []
    list2 = []
    
    #recurse through elements for each pydicom dataset, add some attributes to list for each
    def recurse1(ds):
        for elem in ds:
            if elem.VR == 'SQ':
                [recurse1(item) for item in elem.value]
            else:
                list1.append({"tag":elem.tag.json_key,"desc":elem.description(), "repval":elem.repval,"value":elem.value })
    def recurse2(ds):
        for elem in ds:
            if elem.VR == 'SQ':
                [recurse2(item) for item in elem.value]
            else:
                list2.append({"tag":elem.tag.json_key,"desc":elem.description(), "repval":elem.repval,"value":elem.value })
    recurse1(img1)
    recurse2(img2)
    
    # list out tags and descriptions found in each image
    tags1 = [item["tag"] for item in list1]
    tags2 = [item["tag"] for item in list2]
    
    descs1 = [item["desc"] for item in list1]
    descs2 = [item["desc"] for item in list2]
    
    # use set to remove duplicates
    descs1 = set(descs1)
    descs2 = set(descs2)
    
    #get all possible tags from both images
    tagsadded = tags1 + tags2
    addedset = set(tagsadded)
    
    #list those found in image1 and those found in image2
    foundIn1 = [x for x in tagsadded if x in tags1]
    foundIn2 = [x for x in tagsadded if x in tags2]
    
    #Build new list of (tag, description, image1value, image2value) filling "not present" where needed
    items1 = []
    items1.append({"_tag":"0","desc":"Filename","value1":filename1,"value2":filename2})
    for tag in addedset:
        newobj = {}
        if tag in foundIn1:
            item = [item for item in list1 if item["tag"] == tag][0]
            newobj["_tag"] = tag
            newobj["desc"] = item["desc"]
            # newobj["repval1"] = item["repval"]
            
            if "Array" not in item["repval"]:
                if "value" in item.keys():
                    newobj["value1"] = item["value"]
            else:
                newobj["value1"] = item["repval"]
        else:
            newobj["_tag"] = tag
            # newobj["repval1"] = "tag_not_present"
            newobj["value1"] = "tag_not_present"
        if tag in foundIn2:
            item = [item for item in list2 if item["tag"] == tag][0]
            newobj["_tag"] = tag
            newobj["desc"] = item["desc"]
            # newobj["repval2"] = item["repval"]
            if "Array" not in item["repval"]:
                if "value" in item.keys():
                    newobj["value2"] = item["value"]
            else:
                newobj["value2"] = item["repval"]
        else:
            newobj["_tag"] = tag
            # newobj["repval2"] = "tag_not_present"
            newobj["value2"] = "tag_not_present"
    
        if newobj["value1"] == newobj["value2"]:
            newobj["z_same"] = "True"
        else:
            newobj["z_same"] = "False"

        #sort entries by tag# 
        keys = list(newobj.keys())
        keys.sort()
        sorted_newobj = {i: newobj[i] for i in keys}
        items1.append(sorted_newobj)
    
    #create dataframe for visualization, export to html and csv
    df = pd.DataFrame(items1)
    df = df.sort_values(by=["_tag"])

    htmlpath = os.path.join(destpath,f"compared_{timestamp}.html")
    open(htmlpath,"a").close()
    csvpath = os.path.join(destpath,f"compared_{timestamp}.csv")
    open(csvpath,"a").close()
    df.to_html(htmlpath, index=False)
    df.to_csv(csvpath,index=False)
    message = "finished processing, added files: \n"
    message = message + f"{htmlpath} \n"
    message = message + f"{csvpath}"
    tkinter.messagebox.showinfo(title="Finished", message= message)
    #Open file location , this command only works in windows. 
    #Subprocess.Popen() is not available without admin priviledges
    os.startfile(destpath)
    
# except:
#     message = "something went wrong..."
#     tkinter.messagebox.showerror(title="Error", message = message)