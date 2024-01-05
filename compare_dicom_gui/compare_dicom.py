import pydicom
import pandas as pd
import os
from datetime import datetime
import tkinter
from tkinter import filedialog


def openloc(path):
    os.start(path, "open")


root = tkinter.Tk()
root.wm_attributes("-topmost", 1)
root.withdraw()  # hide tkinter root window
message = ""

currdir = os.getcwd()
tempdir = filedialog.askopenfilenames(
    parent=root, initialdir=currdir, title="Please select up to 4 DICOM image files"
)

count = len(tempdir)

# try:
if count == 0 or count > 4:
    message = f"Invalid Number of Files: Please select between 2 and 4 DICOM images for comparison..."
    tkinter.messagebox.showerror(title="Error", message=message)

if count > 1:
    # set path of image1 and image2 to be compared
    path1 = tempdir[0]
    destpath = os.path.dirname(path1)
    path2 = tempdir[1]
    filename1 = os.path.basename(path1)
    filename2 = os.path.basename(path2)
    # read image with pydicom
    img1 = pydicom.dcmread(path1)
    img2 = pydicom.dcmread(path2)
    list1 = []
    list2 = []

    # recurse through elements for each pydicom dataset, add some attributes to list for each
    def recurse1(ds):
        for elem in ds:
            if elem.VR == "SQ":
                [recurse1(item) for item in elem.value]
            else:
                list1.append(
                    {
                        "tag": elem.tag.json_key,
                        "desc": elem.description(),
                        "repval": elem.repval,
                        "value": elem.value,
                    }
                )

    def recurse2(ds):
        for elem in ds:
            if elem.VR == "SQ":
                [recurse2(item) for item in elem.value]
            else:
                list2.append(
                    {
                        "tag": elem.tag.json_key,
                        "desc": elem.description(),
                        "repval": elem.repval,
                        "value": elem.value,
                    }
                )

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
    # get all possible tags from both images
    tagsadded = tags1 + tags2

    if count > 2:
        path3 = tempdir[2]
        filename3 = os.path.basename(path3)
        img3 = pydicom.dcmread(path3)
        list3 = []

        def recurse3(ds):
            for elem in ds:
                if elem.VR == "SQ":
                    [recurse3(item) for item in elem.value]
                else:
                    list3.append(
                        {
                            "tag": elem.tag.json_key,
                            "desc": elem.description(),
                            "repval": elem.repval,
                            "value": elem.value,
                        }
                    )

        recurse3(img3)
        tags3 = [item["tag"] for item in list3]
        descs3 = [item["desc"] for item in list3]
        descs3 = set(descs3)
        tagsadded = tagsadded + tags3

        if count == 4:
            path4 = tempdir[3]
            filename4 = os.path.basename(path4)
            img4 = pydicom.dcmread(path4)
            list4 = []

            def recurse4(ds):
                for elem in ds:
                    if elem.VR == "SQ":
                        [recurse4(item) for item in elem.value]
                    else:
                        list4.append(
                            {
                                "tag": elem.tag.json_key,
                                "desc": elem.description(),
                                "repval": elem.repval,
                                "value": elem.value,
                            }
                        )

            recurse4(img4)
            tags4 = [item["tag"] for item in list4]
            descs4 = [item["desc"] for item in list4]
            descs4 = set(descs4)
            tagsadded = tagsadded + tags4

    # use current working directory for output files, change if needed.
    # destpath = os.getcwd()

    # generate timestamp for filename
    now = datetime.now()
    timestamp = now.strftime("%m%d%y_%H%M%S")

    # get all possible tags from both images
    addedset = set(tagsadded)

    # list those found in image1 and those found in image2
    foundIn1 = [x for x in tagsadded if x in tags1]
    foundIn2 = [x for x in tagsadded if x in tags2]
    if count > 2:
        foundIn3 = [x for x in tagsadded if x in tags3]
    if count == 4:
        foundIn4 = [x for x in tagsadded if x in tags4]

    # Build new list of (tag, description, image1value, image2value) filling "not present" where needed
    items1 = []
    items1.append(
        {
            "_tag": "0",
            "desc": "Filename",
            "value1": filename1,
            "value2": filename2,
        }
    )
    if count > 2:
        items1[0]["value3"] = filename3
    else:
        items1[0]["value3"] = "none"

    if count > 3:
        items1[0]["value4"] = filename4
    else:
        items1[0]["value4"] = "none"

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

        if count > 2 and tag in foundIn3:
            item = [item for item in list3 if item["tag"] == tag][0]
            newobj["_tag"] = tag
            newobj["desc"] = item["desc"]
            # newobj["repval3"] = item["repval"]
            if "Array" not in item["repval"]:
                if "value" in item.keys():
                    newobj["value3"] = item["value"]
            else:
                newobj["value3"] = item["repval"]
        else:
            newobj["_tag"] = tag
            # newobj["repval3"] = "tag_not_present"
            newobj["value3"] = "tag_not_present"

        if count > 3 and tag in foundIn4:
            item = [item for item in list4 if item["tag"] == tag][0]
            newobj["_tag"] = tag
            newobj["desc"] = item["desc"]
            # newobj["repval4"] = item["repval"]
            if "Array" not in item["repval"]:
                if "value" in item.keys():
                    newobj["value4"] = item["value"]
            else:
                newobj["value4"] = item["repval"]
        else:
            newobj["_tag"] = tag
            # newobj["repval4"] = "tag_not_present"
            newobj["value4"] = "tag_not_present"

        if count == 2:
            if newobj["value1"] == newobj["value2"]:
                newobj["z_same"] = "True"
            else:
                newobj["z_same"] = "False"
        if count == 3:
            if newobj["value1"] == newobj["value2"] == newobj["value3"]:
                newobj["z_same"] = "True"
            else:
                newobj["z_same"] = "False"

        if count == 4:
            if (
                newobj["value1"]
                == newobj["value2"]
                == newobj["value3"]
                == newobj["value4"]
            ):
                newobj["z_same"] = "True"
            else:
                newobj["z_same"] = "False"

        # sort entries by tag#
        keys = list(newobj.keys())
        keys.sort()
        sorted_newobj = {i: newobj[i] for i in keys}
        items1.append(sorted_newobj)

    if count < 4:
        for item in items1:
            del item["value4"]
            if count < 3:
                del item["value3"]

    # create dataframe for visualization, export to html and csv
    df = pd.DataFrame(items1)
    df = df.sort_values(by=["_tag"])

    htmlpath = os.path.join(destpath, f"compared_{timestamp}.html")
    open(htmlpath, "a").close()
    csvpath = os.path.join(destpath, f"compared_{timestamp}.csv")
    open(csvpath, "a").close()
    df.to_html(htmlpath, index=False)
    df.to_csv(csvpath, index=False)
    message = "finished processing, added files: \n"
    message = message + f"{htmlpath} \n"
    message = message + f"{csvpath}"
    tkinter.messagebox.showinfo(title="Finished", message=message)
    # Open file location , this command only works in windows.
    # Subprocess.Popen() is not available without admin priviledges
    os.startfile(destpath)

# except:
#     message = "something went wrong..."
#     tkinter.messagebox.showerror(title="Error", message = message)
