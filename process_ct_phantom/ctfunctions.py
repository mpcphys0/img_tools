import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import pydicom
import cv2
import sys
import glob
import os
import pprint

np.set_printoptions(threshold=sys.maxsize)
import errno
from scipy.ndimage import rotate
from types import SimpleNamespace
from math import dist, radians
import pandas as pd
import pydash
from scipy.signal import find_peaks
from IPython.display import display, Markdown
from skimage.measure import profile_line
from pretty_html_table import build_table
import re
import zipfile
import shutil
import base64
import io
from jinja2 import Template
import ipywidgets as widgets
from datetime import datetime
import csv


def test_print():
    print("ctfunctions.py connected and working", "\U0001F60E")


transfer_syntaxes = [
    {
        "name": "Explicit VR Little Endian",
        "uid": "1.2.840.10008.1.2.1",
        "supported": True,
        "compressed": False,
    },
    {
        "name": "Implicit VR Little Endian",
        "uid": "1.2.840.10008.1.2",
        "supported": True,
        "compressed": False,
    },
    {
        "name": "Explicit VR Big Endian",
        "uid": "1.2.840.10008.1.2.2",
        "supported": True,
        "compressed": False,
    },
    {
        "name": "Deflated Explicit VR Little Endian",
        "uid": "1.2.840.10008.1.2.1.99",
        "supported": True,
        "compressed": False,
    },
    {
        "name": "RLE Lossless",
        "uid": "1.2.840.10008.1.2.5",
        "supported": True,
        "compressed": True,
    },
    {
        "name": "JPEG Baseline (Process 1)",
        "uid": "1.2.840.10008.1.2.4.50",
        "supported": True,
        "compressed": True,
    },
    {
        "name": "JPEG Extended (Process 2 and 4)",
        "uid": "1.2.840.10008.1.2.4.51",
        "supported": True,
        "compressed": True,
    },
    {
        "name": "JPEG Lossless (Process 14)",
        "uid": "1.2.840.10008.1.2.4.57",
        "supported": True,
        "compressed": True,
    },
    {
        "name": "JPEG Lossless (Process 14, SV1)",
        "uid": "1.2.840.10008.1.2.4.70",
        "supported": True,
        "compressed": True,
    },
    {
        "name": "JPEG LS Lossless",
        "uid": "1.2.840.10008.1.2.4.80",
        "supported": True,
        "compressed": True,
    },
    {
        "name": "JPEG LS Lossy",
        "uid": "1.2.840.10008.1.2.4.81",
        "supported": True,
        "compressed": True,
    },
    {
        "name": "JPEG2000 Lossless",
        "uid": "1.2.840.10008.1.2.4.90",
        "supported": True,
        "compressed": True,
    },
    {
        "name": "JPEG2000",
        "uid": "1.2.840.10008.1.2.4.91",
        "supported": True,
        "compressed": True,
    },
    {
        "name": "JPEG2000 Multi-component Lossless",
        "uid": "1.2.840.10008.1.2.4.92",
        "supported": False,
        "compressed": True,
    },
    {
        "name": "JPEG2000 Multi-component",
        "uid": "1.2.840.10008.1.2.4.93",
        "supported": False,
        "compressed": True,
    },
]


def get_SOP_class(imgpath):
    try:
        img = pydicom.dcmread(imgpath)
        sop_class = img[0x00080016].repval
        return sop_class
    except:
        return f"error reading image file {os.path.basename(imgpath)}"


def xy_from_polar(r: float, theta: float, midpoint: tuple[int, int]):
    """
    Convert a polar coordinate to cartesian in the 2D image coordinate system (x,y zero at top left, y increases down)
    using a given polar origin

    Parameters
    ----------
    r = radius in pixels
    theta = angle in radians from vertical y-axis
    midpoint = (x,y) coordinate of reference origin (i.e. phantom center)

    Returns
    -------
    xy : (int,int) cartesian coordinate of point

    """
    xy = int(midpoint[0] + r * np.sin(theta)), int(midpoint[1] - r * np.cos(theta))
    return xy


def get_filtered_peaks(
    pixels, pts_list, resc_slope=1, resc_int=1, px_spacing=1, thresh=0.5
):
    """
    This function takes in an array of sets of two points ((x1,y1),(x2,y2)). For each set, it draws a line profile
    between the points, plots it, and counts the peaks for which the peak magnitude is greater than
    thresh * (profile max - profile min).

    Parameters
    ----------
    pixels: 2D image array
    pts_list: an array of pairs of (x,y) points in the form [((x1,y1),(x2,y2)) , ... ]
    resc_slope: rescale slope (default = 1)
    resc_int: rescale intercept (default = 1)
    px_spacing: square pixel side dimension in mm or other distance unit (default = 1)
    thresh: threshold for counting peaks in line profile. (i.e. set to 0.5, peaks greater than
    50% of max-min intensity will be counted)

    Returns
    -------
    return_value : (results_data, plot1, plot2)
    results_data : [{xpts:list of x axis points in 1D profile}, {ypts: list of pixel values / y axis profile points}, {xfiltered: xpts which exceed threshold},{yfiltered: ypts which exceed threshold},{threshold: threshold in pixel value scale}, {average: average number of peaks from all line profiles}]
    plot1:
    """
    results = []
    lengths = []
    pixels = (resc_slope * pixels) + resc_int
    labels = ["Top Left", "Top Right", "Bottom Left", "Bottom Right"]
    colors = ["r", "g", "b", "y"]
    fig1, ax1 = plt.subplots(1, 1, figsize=(7.8, 7.8))
    fig2, ax2 = plt.subplots(nrows=2, ncols=2, figsize=(7, 7), sharey=True)
    for idx, item in enumerate(pts_list):
        x1, y1, x2, y2 = (
            pts_list[idx][0][0],
            pts_list[idx][0][1],
            pts_list[idx][1][0],
            pts_list[idx][1][1],
        )
        prof = profile_line(pixels, (y1, x1), (y2, x2))
        dist = np.linalg.norm(np.array((x1, y1)) - np.array((x2, y2)))
        dist_mm = dist * px_spacing
        xpts = np.linspace(
            0, dist_mm, len(prof)
        )  # create 1D spatial location array in mm
        min = prof.min()
        max = prof.max()
        peaks_indices = find_peaks(prof)[0]
        peaks = np.array(list(zip(peaks_indices, prof[peaks_indices])))
        threshold = min + thresh * (max - min)
        filtered_peaks = [(index, value) for index, value in peaks if value > threshold]
        filtered_peaks_indices = [index for index, value in peaks if value > threshold]
        lengths.append(len(filtered_peaks_indices))
        filtered_peaks_values = [value for index, value in peaks if value > threshold]
        results.append(
            {
                "label": labels[idx],
                "xpts": xpts,
                "ypts": prof,
                "xfiltered": filtered_peaks_indices,
                "yfiltered": filtered_peaks_values,
                "threshold": threshold,
            }
        )
        # axs.flat[idx].title(f"Found: {len(filtered_peaks_values)} bars")
        ax2.flat[idx].plot(prof, color=colors[idx])
        if idx % 2 == 0:
            ax2.flat[idx].set_ylabel("CT Number (HU)")
        ax2.flat[idx].tick_params(bottom=False, labelbottom=False)
        ax2.flat[idx].axhline(threshold)
        ax2.flat[idx].scatter(filtered_peaks_indices, filtered_peaks_values, s=40)
        ax2.flat[idx].set_title(f"{labels[idx]}: {len(filtered_peaks_indices)} Bars")
        ax1.imshow(pixels, cmap="gray", vmin=-200, vmax=200)
        ax1.plot((x1, x2), (y1, y2), color=colors[idx])
        ax1.axis("Off")
    mod1img1 = encode_figure(fig1)
    mod1img2 = encode_figure(fig2)
    plt.show()

    avg = np.mean(lengths)
    results.append({"avg": avg})
    return results, mod1img1, mod1img2


def handle_compression(file):
    """
    takes in either a pydicom.dataset.FileDataset or a raw dicom image file path.
    Checks if pixel data is compressed and attempts to decompress and
    return the uncompressed dataset or dicom file. If uncompressed data is found,
    original is returned.

    Parameters:
    ----
    filedataset: pydicom.
    """
    if isinstance(file, str):
        try:
            img = pydicom.dcmread(file)
        except:
            print(f"problem reading image file:{file}")
            return
    elif isinstance(file, pydicom.dataset.FileDataset):
        img = file
    else:
        print(f"invalid input to handle_compression:")
        print(f"{file}")
        return
    stx = img.file_meta.TransferSyntaxUID or ""
    if stx != "":
        entry = [x for x in transfer_syntaxes if x["uid"] == stx]
        name = entry[0]["name"]
        supported = entry[0]["supported"]
        compressed = entry[0]["compressed"]
        if supported and compressed:
            try:
                img.decompress(handler_name="gdcm")
                return img
            except:
                print(f"decompression error, returning original pixel data...")
                return img
        elif supported and not compressed:
            return img
        else:
            print(
                f"Pixel data transfer syntax not found or unknown, returning original pixel data..."
            )
            return img

    else:
        print(
            f"Pixel data transfer syntax not found or unknown, returning original pixel data... "
        )
        return img


def local_unzip_contents(zip_path, unzip_path):
    """
    Search zip_path for zip files and then extract them to new folders with same name as original zip in unzip_path

    Paramaters
    ----
    unzip_path: string, path to folder containing zip files
    zip_path: string, path to folder to extract files to

    Returns
    ----
    void / none
    """
    if len(os.listdir(zip_path)) == 0:
        print("No files found in upload folder. \nPlease upload a zip and try again.")
        return
    officeextensions = [".xlsx", ".docx", ".pptx"]
    # list all files in folder
    files = os.listdir(zip_path)
    # make list of non-hidden file and non-MS-office zip file paths.
    target_paths = [
        f"{zip_path}\\{x}"
        for x in files
        if not x.startswith(".") and os.path.splitext(x)[1] not in officeextensions
    ]
    # get filenames
    target_filenames = [os.path.basename(x) for x in target_paths]
    # check if each file is a valid zip
    valid_zips = [x for x in target_paths if zipfile.is_zipfile(x)]
    valid_filenames = [os.path.basename(x) for x in valid_zips]
    print("Valid zip files found:")
    pprint.pp(valid_filenames)
    # make an unzip destination folder if it doesn't already exist
    if not os.path.exists(unzip_path):
        os.mkdir(unzip_path)
    try:
        for file in valid_zips:
            with zipfile.ZipFile(file, "r") as newzip:
                # create new folder with same name as zip and extract contents to it
                unzip_dirname = os.path.splitext(os.path.basename(newzip.filename))[0]
                newzip.extractall(os.path.join(unzip_path, unzip_dirname))
        print("Finished unzipping files to specified directory.")
    except zipfile.BadZipFile:
        print("Error: BadZipFile exception... ")
    except:
        print("Error extracting archives...")


# newdirs = os.listdir(unzip_path)
# newdirpaths = [os.path.join(unzip_path,d) for d in newdirs]


def local_separate_name_images(src_path, dest_path):
    """
    Searches source path for folders, parses each folder to find dicom images.
    Creates new folder for each series, places images named with SliceLocation in each series folder
    """
    # generate timestamp for unique naming purposes
    timestamp = datetime.today().strftime("%Y%m%d%H%M%S")
    # list folders found in source_path
    imgdirs = [
        dirname
        for dirname in os.listdir(src_path)
        if os.path.isdir(os.path.join(src_path, dirname))
    ]

    for folderindex, imgdir in enumerate(imgdirs):
        # list all files down the folder tree
        all_files = [
            os.path.join(dirpath, f)
            for (dirpath, dirnames, filenames) in os.walk(
                os.path.join(src_path, imgdir)
            )
            for f in filenames
        ]

        files_to_process = []

        # add files found to be valid dicom to files_to_process
        print("found", len(all_files), "files in folder:", imgdir)
        decompress_count = 0
        for file in all_files:
            try:
                img = pydicom.dcmread(file)
                if isinstance(img, pydicom.dicomdir.DicomDir):
                    print("Excluding DicomDir:", file)
                elif not hasattr(img, "SliceLocation"):
                    print(
                        os.path.basename(file),
                        " has no SliceLocation attribute, skipping...",
                    )
                else:
                    img = handle_compression(img)
                    files_to_process.append(img)
                    decompress_count = decompress_count + 1
            except pydicom.InvalidDicomError:
                print(f"invalid DICOM error:{file}...")
            except:
                pass
        if decompress_count > 0:
            print(f"Decompressed {decompress_count} files...")
        print("found", len(files_to_process), "DICOM files to process...")

        # sort by slice location
        files_to_process = sorted(files_to_process, key=lambda s: s.SliceLocation)

        uids = []
        descriptions = []
        tuples = []

        for slice in files_to_process:
            # generate list of unique values for series instance uid
            if slice.SeriesInstanceUID not in uids:
                uids.append(slice.SeriesInstanceUID)
            # generate list of unique values for series description
            if hasattr(slice, "SeriesDescription"):
                if slice.SeriesDescription not in descriptions:
                    descriptions.append(slice.SeriesDescription)
            # generate list of tuple(series uid, description, dicom image)
            tuples.append(
                (slice.SeriesInstanceUID, slice.SeriesDescription or "_", slice)
            )
        # blank list for adding entries of (UID, description, [images])
        groups = []

        # If number of series instances is equal to number of series descriptions, add both to new item:
        for i in range(0, len(uids)):
            groups.append((uids[i], [], []))
        for group in groups:
            group_uid = group[0]
            for tuple in tuples:
                if tuple[0] == group_uid:
                    group[2].append(tuple[2])
        dicts = []
        for item in groups:
            if len(item) == 3:
                dicts.append(
                    {"uid": item[0], "description": item[1], "images": item[2]}
                )
            else:
                dicts.append({"uid": item[0], "description": "_", "images": item[1]})

        for idx, entry in enumerate(dicts):
            descr = pydash.kebab_case(entry["description"])
            parentfolder = os.path.join(dest_path, imgdir)
            foldername = f"Series{idx}-{descr}"
            folderpath = os.path.join(parentfolder, foldername)
            if not os.path.exists(folderpath):
                print(f"Creating folder {folderpath}")
                os.makedirs(folderpath)
            imgcount = 0
            for idx, img in enumerate(entry["images"]):
                filepath = os.path.join(
                    folderpath, f"Image{idx}_loc{img.SliceLocation}"
                )
                pydicom.dcmwrite(filepath, img)
                imgcount += 1
            print(f"Added {imgcount} images")


def unzip_and_separate(zip_path: str, unzip_path: str):
    """
    Search the contents of a zip file for valid DICOM images, skips over images
    without SliceLocation attribute (like scout localizers), and then separates all images into
    folders based on their series description or series uid. Individual image files are renamed
    by an index and the SliceLocation of the image. Original unzipped contents are placed in /unzip_path/unzipped/
    and newly separated and named images are placed in /unzip_path/new/

    Parameters
    ----------
    zip_path: directory path containing one zip file with dicom images
    unzip_path: directory path for placing unzipped files and named, separated images

    """
    if len(os.listdir(zip_path)) == 0:  # check if any files have been uploaded
        print("No files found in upload folder. \nPlease upload a zip and try again.")
        return
    if len(os.listdir(zip_path)) >= 1:
        files = os.listdir(zip_path)
        nonhidden = [[x] for x in files if not x.startswith(".")]
        if len(nonhidden) == 0:
            print(
                "No files found in upload folder. \nPlease upload a zip and try again."
            )
            return
        if len(nonhidden) > 1:
            print(
                "Multiple files found in uploads folder. \nPlease delete all but the file to be processed and try again."
            )
            return
        if len(nonhidden) == 1:
            first_file = nonhidden[0][0]
            zip_path = f"{zip_path}{first_file}"
            if os.path.exists(unzip_path):
                shutil.rmtree(unzip_path)
            os.mkdir(unzip_path)
            if zipfile.is_zipfile(zip_path):
                with zipfile.ZipFile(zip_path, "r") as zipref:
                    zipref.extractall(f"{unzip_path}unzipped")
                    print("unzipping...")

            files = []

            list = [
                os.path.join(dirpath, f)
                for (dirpath, dirnames, filenames) in os.walk(unzip_path)
                for f in filenames
            ]

            for file in list:
                try:
                    read = pydicom.dcmread(file)
                    if isinstance(read, pydicom.dicomdir.DicomDir):
                        print("Excluding:", file)
                    else:
                        files.append(read)
                except:
                    pass
            print("found DICOM files:", len(files))
            slices = []

            # identify slices like localizers that don't have SliceLocation and skip them
            skipcount = 0
            for f in files:
                if hasattr(f, "SliceLocation"):
                    slices.append(f)
                else:
                    skipcount = skipcount + 1
            if skipcount > 0:
                print(
                    "skipped",
                    skipcount,
                    "slices due to absence of SliceLocation attribute...",
                )

            slices = sorted(slices, key=lambda s: s.SliceLocation)

            if hasattr(slices[0], "InstitutionName"):
                name = slices[0].InstitutionName
            else:
                name = slices[0].InstiutionCodeSequence
            # name = pydash.capitalize(pydash.camel_case(name), strict=False)
            # date = pydash.camel_case(slices[0].StudyDate)
            # model =  pydash.capitalize(pydash.camel_case(slices[0].ManufacturerModelName), strict=False)
            # namestring = f"{date}_{name}_{model}_images"
            uids = []
            descriptions = []
            tuples = []

            for slice in slices:
                # generate list of unique values for series instance uid
                if slice.SeriesInstanceUID not in uids:
                    uids.append(slice.SeriesInstanceUID)
                # generate list of unique values for series description
                if hasattr(slice, "SeriesDescription"):
                    if slice.SeriesDescription not in descriptions:
                        descriptions.append(slice.SeriesDescription)
                # generate list of (series uid, description, dicom image)
                tuples.append((slice.SeriesInstanceUID, slice.SeriesDescription, slice))
            # blank list for adding entries of (UID, description, [images])
            groups = []

            # If number of series instances is equal to number of series descriptions, add both to new item:

            for i in range(0, len(uids)):
                if len(uids) == len(descriptions):
                    # add (uid, description, blank list)
                    groups.append((uids[i], descriptions[i], []))
                else:
                    groups.append((uids[i], descriptions[i], []))
            for group in groups:
                group_uid = group[0]
                for tuple in tuples:
                    if tuple[0] == group_uid:
                        group[2].append(tuple[2])

            # print(len(groups[3][2]))
            dicts = []
            for item in groups:
                if len(item) == 3:
                    dicts.append(
                        {"uid": item[0], "description": item[1], "images": item[2]}
                    )
                else:
                    dicts.append(
                        {"uid": item[0], "description": "_", "images": item[1]}
                    )

            destpath = f"{unzip_path}new"
            if os.path.exists(destpath):
                shutil.rmtree(destpath)
            os.mkdir(destpath)

            for idx, entry in enumerate(dicts):
                descr = pydash.kebab_case(entry["description"])
                foldername = f"{idx}-{descr}"
                folderpath = f"{destpath}/{foldername}"
                print(f"Creating folder {folderpath}")
                os.mkdir(folderpath)
                imgcount = 0
                for idx, img in enumerate(entry["images"]):
                    filepath = f"{folderpath}/Image{idx}_loc{img.SliceLocation}"
                    pydicom.dcmwrite(filepath, img)
                    imgcount += 1
                print(f"Added {imgcount} images")

            shutil.make_archive("Separated-Named-Images", "zip", destpath)
            print(
                "\nCompleted unzipping and separating image files. \nImages can be found in images/new/. \n A zip file of all images has been saved in the main directory. \nProceed to next cell."
            )


def load_multiple_dicom(path: str):
    """
    path: path to a directory containing DICOM images
    --
    Takes path string of folder containing only DICOM files with any extension \n
    remove dicomdir, other files first.
    Returns a list of pydicom.dataset.FileDataset
    """
    if os.path.exists(path):
        files = []
        for fname in glob.glob(f"{path}/*", recursive=True):
            file = pydicom.dcmread(fname)
            files.append(file)
        return files
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)


def get_slices(source_path: str, rotate_angle=0):
    """
    Search a folder of DICOM images, extract those with SliceLocation attribute, sorted by SliceLocation

    Parameters
    ----------
    source_path : path to directory containing DICOM images
    rotate_angle : set an angle to rotate all images in degrees

    Returns
    -------
    slices : list of pydicom.dataset.FileDataset

    """
    files = load_multiple_dicom(
        source_path
    )  # slices is a list of pydicom.dataset.FileDataset

    slices = []
    # identify slices like localizers that don't have SliceLocation and skip them
    skipcount = 0
    for f in files:
        if hasattr(f, "SliceLocation"):
            slices.append(f)
        else:
            skipcount = skipcount + 1
    # print("skipped",skipcount, "slices")
    if rotate_angle != 0:
        for slice in slices:
            pixels = slice.pixel_array
            rotated = rotate(pixels, angle=rotate_angle, reshape=False)
            slice.PixelData = rotated.tobytes()
    slices = sorted(slices, key=lambda s: s.SliceLocation)
    return slices


def get_slice_increase(distance: float, thickness: float):
    """
    Find optimal number of slices to add to starting point to get closest to a particular phantom location

    Parameters
    ----------
    distance : location of desired phantom slice location in same units as slice thickness (i.e. 40 to get to low contrast module of Gammex phantom)
    thickness : slice thickness of images

    Returns
    -------
    number : number of slices to add to get to desired location
    """
    distance = distance
    thik = thickness
    number = distance // thik
    nextnum = number + 1
    diffnum = np.abs(distance - number * thik)
    diffnext = np.abs(distance - nextnum * thik)
    if diffnum < diffnext:
        return number
    else:
        return nextnum


def get_slice_coordinates(slices: list, show_plots=False):
    """
    Takes a set of phantom images spanning the full distance of the ACR Gammex Phantom (at least from 0 to 120mm),
    draws ROIs through all slices to search for top BBs, bottom BBs, 12lp/cm line pair set in Module 4,
    phantom center, and top diagonal BB in Module 3. Based on pixel values in ROI search, determines a slice location
    and phantom position for each of the four modules.

    Parameters
    ----------
    slices: list of pydicom.dataset.FileDataset
    show_plots: bool, show additional plots of placement of various points and ROIs

    Returns
    -------
    slice_coords : list of
    [{"slice": pydicom.dataset.FileDataset, "loc": float, "top": (int,int), "bot": (int,int)},...]
    Where \n
    "slice" is the DICOM image,\n
    "loc" is the SliceLocation of the image,\n
    "top" is the (x,y) coordinate of the top BB,\n
    "bot" is (x,y) coordinate of bottom BB\n
    slice_coords[0] -> Slice at Module 1\n
    slice_coords[1] -> Module 2\n
    slice_coords[2] -> Module 3\n
    slice_coords[3] -> Module 4\n
    """

    slices = sorted(slices, key=lambda s: s.SliceLocation)
    slice_thickness = slices[0].SliceThickness
    resc_int = slices[0].RescaleIntercept
    resc_slope = slices[0].RescaleSlope
    points = []
    bot_points = []
    lp_points = []
    center_points = []
    dist_top_points = []
    first_slice_pixels = slices[0].pixel_array
    width = first_slice_pixels.shape[0]
    height = first_slice_pixels.shape[1]
    # determine points that define rectangular ROIs:
    # Top BB search
    xtop1 = int(width * 3 / 7)
    ytop1 = 0
    xtop2 = int(width * 4 / 7)
    ytop2 = int(height / 11)
    # Bottom BB search
    xbot1 = int(width * 3 / 7)
    ybot1 = int(height * 10 / 11)
    xbot2 = int(width * 4 / 7)
    ybot2 = int(height)
    # 12 lp/cm line pair search (module 4)
    linepair_x1 = int(width * 3 / 7)
    linepair_x2 = int(width * 4 / 7)
    linepair_y1 = int(height / 11)
    linepair_y2 = int(height * 2 / 11)
    # phantom center ROI
    centerx1 = xtop1
    centerx2 = xtop2
    centery1 = int(height * 5 / 11)
    centery2 = int(height * 6 / 11)
    # Top diagonal distance BB search (module 3)
    disttopx1 = int(width * 1 / 3)
    disttopx2 = int(width * 2 / 3)
    disttopy1 = int(height * 1 / 3)
    disttopy2 = int(height * 2 / 3)

    ROIs = []
    enm = enumerate(slices)
    for idx, slice in enm:
        pixels = slice.pixel_array
        # define ROIs:
        # roi -> top BB, roi_bot -> bottom BB, roi_lp -> module 4 line pair ROI, roi_center -> phantom center ROI
        # roi_dist_top -> top distance BB ROI, roi_dist_bot-> bottom distance BB ROI
        roi = pixels[
            ytop1:ytop2, xtop1:xtop2
        ]  # caution this slicing is in (rows,columns) format
        roi_bot = pixels[
            ybot1:ybot2, xbot1:xbot2
        ]  # caution this slicing is in (rows, columns) fromat
        roi_lp = pixels[linepair_y1:linepair_y2, linepair_x1:linepair_x2]
        roi_center = pixels[centery1:centery2, centerx1:centerx2]
        roi_dist_top = pixels[disttopy1:disttopy2, disttopx1:disttopx2]

        # get max or mean values from various ROIs:
        roi_max = resc_slope * (roi.max() + resc_int)
        roi_bot_max = resc_slope * (roi_bot.max() + resc_int)
        lp_mean = resc_slope * (roi_lp.mean() + resc_int)
        center_mean = resc_slope * (roi_center.mean() + resc_int)
        dist_top_max = resc_slope * (roi_dist_top.max() + resc_int)

        # add all ROIs to ROIs array:
        ROIs.append(
            {
                "idx": idx,
                "loc": slice.SliceLocation,
                "top_max": roi_max,
                "top_pixels": roi,
                "bot_max": roi_max,
                "bot_pixels": roi_bot,
                "lp_mean": lp_mean,
                "lp_pixels": roi_lp,
                "center_mean": center_mean,
                "center_pixels": roi_center,
                "dist_top_max": dist_top_max,
                "dist_top_pixels": roi_dist_top,
            }
        )

        # Add points to points arrays, for plotting value vs slice location
        points.append((float(slice.SliceLocation), roi_max))
        bot_points.append((float(slice.SliceLocation), roi_bot_max))
        lp_points.append((float(slice.SliceLocation), lp_mean))
        center_points.append((float(slice.SliceLocation), center_mean))
        dist_top_points.append((float(slice.SliceLocation), dist_top_max))
    chinBBs = []
    headBBs = []
    singleBBs = []
    distBBs = []
    for roi in ROIs:
        # If slice has a top and bottom BB (signal > 200 HU in BB ROIs)
        if roi["top_max"] > 200 and roi["bot_max"] > 200:
            # determine if slice has line pairs (corresponding to 120 / module 4)
            if roi["lp_mean"] > 150:
                # add a value for the combined max of top and bottom BB
                roi["top_bot_max"] = roi["top_max"] + roi["bot_max"]
                headBBs.append(roi)
            # else if slices are at the chin end:
            else:
                roi["top_bot_max"] = roi["top_max"] + roi["bot_max"]
                chinBBs.append(roi)
        # add ROIs for slices with ONLY either a top or bottom BB in case no slices have both:
        if roi["top_max"] > 200 or roi["bot_max"] > 200:
            singleBBs.append(roi)
    if len(chinBBs) == 0:
        if len(singleBBs) > 0:
            # future: insert code for single BB methodology
            print("single bb slice found, run single method...")
            return
        else:
            print("no top/bottom BBs found near chin end...")
            return
    # determine slice progression direction (should almost always be increasing positive)
    # i.e. slice loc value should increase from chin to head end
    # sort chin and head slice sets to get slices with highest top_bottom_max pixel value
    chin_sorted = sorted(chinBBs, key=lambda d: d["top_bot_max"], reverse=True)
    head_sorted = sorted(headBBs, key=lambda d: d["top_bot_max"], reverse=True)
    # find slice location value for the best slice from the sorted sets:
    zero_loc = chin_sorted[0]["loc"]
    onetwenty_loc = head_sorted[0]["loc"]
    if zero_loc < onetwenty_loc:
        increase_positive = True
    else:
        increase_positive = False
    # find list index of 0 and 120 slice in order to drop ends of scan for searching for 80/module 3 slice
    zero_index = [i for i in range(len(slices)) if slices[i].SliceLocation == zero_loc]
    onetwenty_index = [
        i for i in range(len(slices)) if slices[i].SliceLocation == onetwenty_loc
    ]
    images_span = onetwenty_index[0] - zero_index[0]
    front_slices_to_drop = images_span // 2
    end_slices_to_drop = images_span * 5 // 6
    eighty_search_slices = []
    for idx, slice in enumerate(slices):
        if idx > front_slices_to_drop and idx < end_slices_to_drop:
            eighty_search_slices.append(slice)
    eighty_BB_index = np.argmax(
        [
            ROIs[i]["dist_top_max"]
            for i in range(front_slices_to_drop + 1, end_slices_to_drop + 1)
        ]
    )
    eighty_loc = eighty_search_slices[eighty_BB_index].SliceLocation
    # find number of slices to add to get closest to 40 position based on slice thickness
    slices_to_add = get_slice_increase(distance=40, thickness=slice_thickness)
    forty_loc = (
        zero_loc + slices_to_add * slice_thickness
        if increase_positive
        else zero_loc - slices_to_add * slice_thickness
    )

    # get correct slices from slices array based on SliceLocations found above
    zero_slice = next((x for x in slices if x.SliceLocation == zero_loc), None)
    forty_slice = next((x for x in slices if x.SliceLocation == forty_loc), None)
    eighty_slice = next((x for x in slices if x.SliceLocation == eighty_loc), None)
    onetwenty_slice = next(
        (x for x in slices if x.SliceLocation == onetwenty_loc), None
    )

    # define x and y values for optionally plotting ROI signal vs slice location
    xs = [x[0] for x in points]
    ys = [x[1] for x in points]
    botx = [x[0] for x in bot_points]
    boty = [x[1] for x in bot_points]
    lpxs = [x[0] for x in lp_points]
    lpys = [x[1] for x in lp_points]
    cnxs = [x[0] for x in center_points]
    cnys = [x[1] for x in center_points]
    dtxs = [x[0] for x in dist_top_points]
    dtys = [x[1] for x in dist_top_points]

    # plot ROI values against slice location
    if show_plots:
        plt.xlabel("Slice Position")
        plt.ylabel("Pixel Value (HU)")
        plt.plot(xs, ys, label="Top BB Max")
        plt.plot(botx, boty, label="Bottom BB Max")
        plt.plot(lpxs, lpys, label="Line Pairs Mean")
        plt.plot(cnxs, cnys, label="Center Mean")
        plt.plot(dtxs, dtys, label="Top Distance BB Max")
        plt.legend()
        plt.show()
        plt.figure()

    # locate max pixel value location for top and bottom BBs at module 0 and module 4
    top_max_roi_pixels = chin_sorted[0]["top_pixels"]
    top_max_coord = np.unravel_index(
        np.argmax(top_max_roi_pixels), top_max_roi_pixels.shape
    )
    zerotop_x = top_max_coord[1] + xtop1
    zerotop_y = top_max_coord[0] + ytop1
    zerotop = zerotop_x, zerotop_y
    bot_max_roi_pixels = chin_sorted[0]["bot_pixels"]
    bot_max_coord = np.unravel_index(
        np.argmax(bot_max_roi_pixels), bot_max_roi_pixels.shape
    )
    zerobot_x = bot_max_coord[1] + xbot1
    zerobot_y = bot_max_coord[0] + ybot1
    zerobot = zerobot_x, zerobot_y
    total_distance = abs(float(onetwenty_loc) - float(zero_loc))
    onetwenty_rois = next((x for x in ROIs if x["loc"] == onetwenty_loc), None)
    onetwenty_top_pixels = onetwenty_rois["top_pixels"]
    onetwentytop_max_coord = np.unravel_index(
        np.argmax(onetwenty_top_pixels), onetwenty_top_pixels.shape
    )
    onetwentytop_x = onetwentytop_max_coord[1] + xtop1
    onetwentytop_y = onetwentytop_max_coord[0] + ytop1
    onetwentytop = onetwentytop_x, onetwentytop_y
    onetwenty_bot_pixels = onetwenty_rois["bot_pixels"]
    onetwentybot_max_coord = np.unravel_index(
        np.argmax(onetwenty_bot_pixels), onetwenty_bot_pixels.shape
    )
    onetwentybot_x = onetwentybot_max_coord[1] + xbot1
    onetwentybot_y = onetwentybot_max_coord[0] + ybot1
    onetwentybot = onetwentybot_x, onetwentybot_y

    # find tilt and yaw of phantom from front to back using top and bottom BB coordinates:
    # adjust top and bottom positions of modules 2 and 3 based on phantom tilt and yaw
    top_rise = (zerotop_x - onetwentytop_x) / (
        total_distance
    )  # pixels/mm along z-direction
    top_yaw = (zerotop_y - onetwentytop_y) / (
        total_distance
    )  # pixels/mm along z-direction
    bot_rise = (zerobot_x - onetwentybot_x) / (total_distance)  # same for bottom
    bot_yaw = (zerobot_y - onetwentybot_y) / (total_distance)  # same for bottom
    fortytop_x = abs(forty_loc - zero_loc) * top_yaw + zerotop_x  # x pixel top at 40
    fortytop_y = abs(forty_loc - zero_loc) * top_rise + zerotop_y  # y pixel top at 40
    fortybot_x = abs(forty_loc - zero_loc) * bot_yaw + zerobot_x
    fortybot_y = abs(forty_loc - zero_loc) * bot_rise + zerobot_y
    top_forty = int(fortytop_x), int(fortytop_y)
    bot_forty = int(fortybot_x), int(fortybot_y)
    center_forty = (
        int((fortytop_x + fortybot_x) * 0.5),
        int((fortytop_y + fortybot_y) * 0.5),
    )
    radius_forty = dist((fortytop_x, fortytop_y), (center_forty[0], center_forty[1]))
    eightytop_x = abs(eighty_loc - zero_loc) * top_yaw + zerotop_x
    eightytop_y = abs(eighty_loc - zero_loc) * top_rise + zerotop_y
    eightybot_x = abs(eighty_loc - zero_loc) * bot_yaw + zerobot_x
    eightybot_y = abs(eighty_loc - zero_loc) * bot_rise + zerobot_y
    top_eighty = int(eightytop_x), int(eightytop_y)
    bot_eighty = int(eightybot_x), int(eightybot_y)
    center_eighty = (
        int((eightytop_x + eightybot_x) * 0.5),
        int((eightytop_y + eightybot_y) * 0.5),
    )
    radius_eighty = dist(
        (eightytop_x, eightytop_y), (center_eighty[0], center_eighty[1])
    )

    # optionally plot top and bottom BB for each of the four slices
    if show_plots:
        plt.figure(figsize=(4, 4))
        plt.imshow(zero_slice.pixel_array, cmap="gray")
        plt.plot(zerotop_x, zerotop_y, marker="o")
        plt.plot(zerobot_x, zerobot_y, marker="o")
        plt.show()
        plt.figure(figsize=(4, 4))
        plt.imshow(forty_slice.pixel_array, cmap="gray")
        plt.plot(fortytop_x, fortytop_y, marker="o")
        plt.plot(fortybot_x, fortybot_y, marker="o")
        plt.show()
        plt.figure(figsize=(4, 4))
        plt.imshow(eighty_slice.pixel_array, cmap="gray")
        plt.plot(eightytop_x, eightytop_y, marker="o")
        plt.plot(eightybot_x, eightybot_y, marker="o")
        plt.show()
        plt.figure(figsize=(4, 4))
        plt.imshow(onetwenty_slice.pixel_array, cmap="gray")
        plt.plot(onetwentytop_x, onetwentytop_y, marker="o")
        plt.plot(onetwentybot_x, onetwentybot_y, marker="o")
        plt.show()

        rescale = (
            np.maximum(zero_slice.pixel_array, 0) / zero_slice.pixel_array.max() * 255
        )
        rescale = np.uint8(rescale)

        # optionally plot ROIs on slice zero
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.axis("Off")
        ax.add_patch(
            Rectangle(
                xy=(xtop1, ytop1),
                width=width // 7,
                height=height // 11,
                fill=None,
                color="white",
            )
        )
        ax.add_patch(
            Rectangle(
                xy=(xbot1, ybot1),
                width=width // 7,
                height=height // 11,
                fill=None,
                color="white",
            )
        )
        ax.add_patch(
            Rectangle(
                xy=(linepair_x1, linepair_y1),
                width=width // 7,
                height=height // 7,
                fill=None,
                color="white",
            )
        )
        ax.add_patch(
            Circle(xy=(zerotop_x, zerotop_y), radius=7, fill=False, edgecolor="white")
        )
        ax.add_patch(
            Circle(xy=(zerobot_x, zerobot_y), radius=7, fill=False, edgecolor="white")
        )

        ax.imshow(rescale, cmap="gray")
        plt.show()
        print(
            "Found zero slice (top BB) at position:",
            zero_loc,
            "... Check image for verification.",
        )

        rescale80 = (
            np.maximum(eighty_slice.pixel_array, 0)
            / eighty_slice.pixel_array.max()
            * 255
        )
        rescale80 = np.uint8(rescale80)

        # optionally plot diagonal distance BB search ROI on module 3
        fig2, ax2 = plt.subplots(figsize=(8, 8))
        ax2.axis("Off")
        ax2.add_patch(
            Rectangle(
                xy=(disttopx1, disttopy1),
                width=width // 3,
                height=height // 3,
                fill=None,
                color="white",
            )
        )
        ax2.imshow(rescale80, cmap="gray")
        plt.show()

    slice_coords = [
        {"slice": zero_slice, "loc": zero_loc, "top": zerotop, "bottom": zerobot},
        {"slice": forty_slice, "loc": forty_loc, "top": top_forty, "bottom": bot_forty},
        {
            "slice": eighty_slice,
            "loc": eighty_loc,
            "top": top_eighty,
            "bottom": bot_eighty,
        },
        {
            "slice": onetwenty_slice,
            "loc": onetwenty_loc,
            "top": onetwentytop,
            "bottom": onetwentybot,
        },
    ]

    return slice_coords


def encode_figure(fig):
    """
    Encodes a matplotlib figure into a base64 .png data URI

    Parameters
    ----------
    fig: matplotlib.figure.Figure

    Returns
    -------
    dataURI: string of format "data:image/png;base64,..."
    """
    stringIObytes = io.BytesIO()
    fig.savefig(stringIObytes, format="png", bbox_inches="tight")
    stringIObytes.seek(0)
    my_base64_pngData = base64.b64encode(stringIObytes.read()).decode()
    dataURI = f"data:image/png;base64,{my_base64_pngData}"
    return dataURI


def process_phantom(slice_dict, report_directory="reports/"):
    """
    Processes ACR CT images and saves analysis reports in PDF and CSV format

    Parameters
    ----------
    slice_dict : [
        {\n
            "slice" : pydicom.dataset.FileDataset -> DICOM image slice\n
            "loc" : float -> SliceLocation \n
            "top" : tuple[int,int] -> top BB x,y coordinate \n
            "bot" : tuple[int,int] -> bottom BB x,y coordinate \n
        }
    ] -> list should contain 4 dict elements, one for each module of the ACR Phantom
    report_directory : str, path to reports directory

    """

    title, table = generate_first_page(slice_dict[0]["slice"], report_directory)
    barsdf, ctdf = process_slice_zero(slice_dict, report_directory)
    cnrdf = process_slice_forty(slice_dict, report_directory)
    unifdf, distdf = process_slice_eighty(slice_dict, report_directory)
    moddf, pdf, newfilename = process_slice_onetwenty(slice_dict, report_directory)

    csvlist = []
    lines = []
    table = table.to_csv(report_directory + "table.csv", index=False, header=None)
    csvlist.append(report_directory + "table.csv")
    barsdf = barsdf.to_csv(report_directory + "bars.csv")
    csvlist.append(report_directory + "bars.csv")
    ctdf = ctdf.to_csv(report_directory + "ctdf.csv")
    csvlist.append(report_directory + "ctdf.csv")
    cnrdf = cnrdf.to_csv(report_directory + "cnr.csv")
    csvlist.append(report_directory + "cnr.csv")
    unifdf = unifdf.to_csv(report_directory + "unif.csv")
    csvlist.append(report_directory + "unif.csv")
    distdf = distdf.to_csv(report_directory + "dist.csv")
    csvlist.append(report_directory + "dist.csv")
    moddf = moddf.to_csv(report_directory + "mod.csv")
    csvlist.append(report_directory + "mod.csv")
    for sheet in csvlist:
        lines.append("")
        with open(sheet, "r") as f:
            reader = csv.reader(f, delimiter="\t")
            for i, line in enumerate(reader):
                lines.append(line)
    csvdir = os.path.join(report_directory, "csv/")
    if not os.path.exists(csvdir):
        os.mkdir(csvdir)
    maindir = os.getcwd()
    os.chdir(csvdir)
    with open(newfilename + ".csv", "w+", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter="\t")
        for line in lines:
            writer.writerow(line)
    os.chdir(maindir)
    for file in csvlist:
        os.remove(file)
    pdfdir = os.path.join(report_directory, "pdf/")
    if not os.path.exists(pdfdir):
        os.mkdir(pdfdir)
    for file in os.listdir(report_directory):
        if file.endswith(".pdf"):
            oldpath = os.path.join(report_directory, file)
            newpath = os.path.join(pdfdir, file)
            shutil.move(oldpath, newpath)


def generate_first_page(img, report_directory):
    """
    Generate a main title and info table with basics about the image set being analyzed\n
    Creates reports directory if it doesn't exist

    Parameters
    ----------
    img: pydicom.dataset.FileDataset
    report_directory: string, path to directory for saving reports

    Returns
    -------
    main_title : IPython.display.Markdown -> Main title display text
    df : pandas.DataFrame -> basic info about image set

    """
    if not os.path.exists(report_directory):
        os.makedirs(report_directory)

    full_list = []
    basics = []
    kwds = [
        "StudyDate",
        "InstitutionName",
        "Manufacturer",
        "StationName",
        "ManufacturerModelName",
        "DeviceSerialNumber",
        "SoftwareVersions",
        "SeriesDescription",
        "PatientID",
    ]
    filtered = [x for x in kwds if x in img]

    for idx, elem in enumerate(img):
        if elem.name != "Pixel Data":
            # print([idx, elem.tag,elem.name,elem.value])
            full_list.append([elem.tag, elem.name, elem.value])
            if elem.keyword in filtered:
                if elem.keyword != "StudyDate":
                    basics.append([elem.name, elem.value])
                else:
                    date = elem.value
                    date = date[:4] + "-" + date[4:6] + "-" + date[6:]
                    basics.append([elem.name, date])

    df_ = pd.DataFrame(basics)
    df = df_.copy()
    df_ = df_.style.set_properties(**{"text-align": "left"})
    df_ = df_.hide(subset=None, level=None, names=False)
    df_ = df_.hide(subset=None, level=None, names=False, axis=1)
    html_table_blue_light = build_table(df, "blue_light")
    cleaned_html = re.sub(
        r"<thead>.*?</thead>", "", html_table_blue_light, flags=re.DOTALL
    )

    main_title = Markdown("## ACR CT Phantom Analysis Report")
    display(main_title)
    display(df_)
    display(Markdown('<hr style="width:800px;margin:5px auto 5px 0px;"></hr>'))

    report_path = os.path.join(report_directory, "ct-report.html")
    Func = open(report_path, "w+")
    Func.write("<h4>CT Phantom Analysis Report</h4>")
    Func.write("<hr style='width: 1000px; margin-left: 0px'>")
    Func.write(cleaned_html)
    Func.write("<hr style='width: 1000px; margin-left: 0px'>")
    Func.close()

    return main_title, df


def local_generate_first_page(img, report_directory):
    """
    Generate a main title and info table with basics about the image set being analyzed\n
    Creates reports directory if it doesn't exist

    Parameters
    ----------
    img: pydicom.dataset.FileDataset
    report_directory: string, path to directory for saving reports

    Returns
    -------
    main_title : IPython.display.Markdown -> Main title display text
    df : pandas.DataFrame -> basic info about image set

    """
    if not os.path.exists(report_directory):
        os.makedirs(report_directory)

    full_list = []
    basics = []
    kwds = [
        "StudyDate",
        "InstitutionName",
        "Manufacturer",
        "StationName",
        "ManufacturerModelName",
        "DeviceSerialNumber",
        "SoftwareVersions",
        "SeriesDescription",
        "PatientID",
        "SeriesInstanceUID",
    ]
    filtered = [x for x in kwds if x in img]

    for idx, elem in enumerate(img):
        if elem.name != "Pixel Data":
            # print([idx, elem.tag,elem.name,elem.value])
            full_list.append([elem.tag, elem.name, elem.value])
            if elem.keyword in filtered:
                if elem.keyword != "StudyDate":
                    basics.append([elem.name, elem.value])
                else:
                    date = elem.value
                    date = date[:4] + "-" + date[4:6] + "-" + date[6:]
                    basics.append([elem.name, date])
    studydate = [x[1] for x in basics if x[0] == "Study Date"][0] or "date"
    series = [x[1] for x in basics if x[0] == "Series Description"][0] or "series"
    inst = [x[1] for x in basics if x[0] == "Institution Name"][0] or "institution"
    seriesUID = [x[1] for x in basics if x[0] == "Institution Name"][0][
        -7:
    ] or "seriesUID"

    # rand = "".join(
    #     random.choice(string.digits + string.ascii_letters) for _ in range(5)
    # )
    rpt_name = (
        pydash.camel_case(studydate)
        + "_"
        + pydash.upper_first(pydash.camel_case(inst))
        + "_"
        + pydash.upper_first(pydash.camel_case(series))
        + "_"
        + seriesUID
        + "_"
        + "ct-rpt.html"
    )

    rpt_path = os.path.join(report_directory, rpt_name)

    # if os.path.exists(rpt_path):
    #     rpt_path =

    df_ = pd.DataFrame(basics)
    df = df_.copy()
    df_ = df_.style.set_properties(**{"text-align": "left"})
    df_ = df_.hide(subset=None, level=None, names=False)
    df_ = df_.hide(subset=None, level=None, names=False, axis=1)
    html_table_blue_light = build_table(df, "blue_light")
    cleaned_html = re.sub(
        r"<thead>.*?</thead>", "", html_table_blue_light, flags=re.DOTALL
    )

    main_title = Markdown("## ACR CT Phantom Analysis Report")
    display(main_title)
    display(df_)
    display(Markdown('<hr style="width:800px;margin:5px auto 5px 0px;"></hr>'))

    Func = open(rpt_path, "w+")
    Func.write("<h4>CT Phantom Analysis Report</h4>")
    Func.write("<hr style='width: 1000px; margin-left: 0px'>")
    Func.write(cleaned_html)
    Func.write("<hr style='width: 1000px; margin-left: 0px'>")
    Func.close()

    return main_title, df, rpt_path


def process_slice_zero(slice_dict, html_path):
    """
    Analyzes slice 0 (Module 1 of ACR Gammex Phantom)

    Parameters
    ----------
    slice_dict : [{"slice": pydicom.dataset.FileDataset, "loc": float, "top": (int,int), "bot": (int,int)},...] -> should have 4 elements for modules 1-4
    report_directory : str -> path to reports directory

    Returns
    -------
    barsdf : pandas.DataFrame -> slice thickness line profile counts info
    ctdf : pandas.DataFrame -> ct number measurements
    """
    resc_int = slice_dict[0]["slice"].RescaleIntercept
    resc_slope = slice_dict[0]["slice"].RescaleSlope
    adjpx = slice_dict[0]["slice"].pixel_array
    px_width = slice_dict[0]["slice"].PixelSpacing[0]
    slice_thickness = slice_dict[0]["slice"].SliceThickness
    slice_thickness = "{0:.2f}".format(slice_thickness)
    adjpx = resc_slope * adjpx + resc_int
    topbb = slice_dict[0]["top"]
    botbb = slice_dict[0]["bottom"]
    topx = topbb[0]
    topy = topbb[1]
    botx = botbb[0]
    boty = botbb[1]
    midpoint = (int((topx + botx) * 0.5), int((boty + topy) * 0.5))
    midpoint_distance = dist((topx, topy), (midpoint[0], midpoint[1]))
    xshift = topx - midpoint[0]
    adjacent = np.sqrt((midpoint_distance**2) - (xshift**2))
    rot_angle = np.arctan(xshift / adjacent)
    # use polar transformation to place ROIs in case phantom is rotated
    poly_polar = (midpoint_distance * 0.63, rot_angle + (radians(-45)))
    poly_xy = xy_from_polar(poly_polar[0], poly_polar[1], midpoint)
    bone_polar = (midpoint_distance * 0.63, rot_angle + (radians(45)))
    bone_xy = xy_from_polar(bone_polar[0], bone_polar[1], midpoint)
    acryl_polar = (midpoint_distance * 0.63, rot_angle + (radians(-135)))
    acryl_xy = xy_from_polar(acryl_polar[0], acryl_polar[1], midpoint)
    air_polar = (midpoint_distance * 0.63, rot_angle + (radians(135)))
    air_xy = xy_from_polar(air_polar[0], air_polar[1], midpoint)
    water_polar = (midpoint_distance * 0.63, rot_angle + (radians(-90)))
    water_xy = xy_from_polar(water_polar[0], water_polar[1], midpoint)
    lpR1_polar = (midpoint_distance * (33.5 / 244), rot_angle + (0.464))
    lpR1 = xy_from_polar(lpR1_polar[0], lpR1_polar[1], midpoint)
    lp2R_polar = (midpoint_distance * (214.53 / 244), rot_angle + (0.07))
    lpR2 = xy_from_polar(lp2R_polar[0], lp2R_polar[1], midpoint)
    lpL1_polar = (midpoint_distance * (33.5 / 244), rot_angle - (0.464))
    lpL2_polar = (midpoint_distance * (214.53 / 244), rot_angle - 0.07)
    lpL1 = xy_from_polar(lpL1_polar[0], lpL1_polar[1], midpoint)
    lpL2 = xy_from_polar(lpL2_polar[0], lpL2_polar[1], midpoint)
    lpBotL2_polar = (midpoint_distance * (33.5 / 244), rot_angle + radians(180) + 0.464)
    lpBotL1_polar = (
        midpoint_distance * (214.53 / 244),
        rot_angle + radians(180) + 0.07,
    )
    lpBotL2_xy = xy_from_polar(lpBotL2_polar[0], lpBotL2_polar[1], midpoint)
    lpBotL1_xy = xy_from_polar(lpBotL1_polar[0], lpBotL1_polar[1], midpoint)
    lpBotR2_polar = (
        midpoint_distance * (33.5 / 244),
        rot_angle + radians(180) - (0.464),
    )
    lpBotR1_polar = (
        midpoint_distance * (214.53 / 244),
        rot_angle + radians(180) - (0.07),
    )
    lpBotR2_xy = xy_from_polar(lpBotR2_polar[0], lpBotR2_polar[1], midpoint)
    lpBotR1_xy = xy_from_polar(lpBotR1_polar[0], lpBotR1_polar[1], midpoint)

    display(Markdown('<p style="page-break-before: always"></p>'))
    display(Markdown("## Module 0"))
    display(Markdown("### Slice Thickness"))
    display(
        Markdown(
            f"Line profiles are obtained across the slice thickness ramp bars as shown. "
        )
    )
    display(Markdown(f"Bars with >50% signal are counted and averaged.."))

    # returns peaks data followed by 2 base64 encoded image dataURIs for placing in html report
    newvals, mod1img1, mod1img2 = get_filtered_peaks(
        adjpx,
        [
            (lpL1, lpL2),
            (lpR1, lpR2),
            (lpBotL1_xy, lpBotL2_xy),
            (lpBotR1_xy, lpBotR2_xy),
        ],
        px_spacing=px_width,
    )

    dd = {
        "Polyethylene": (poly_xy[0], poly_xy[1]),
        "Bone": (bone_xy[0], bone_xy[1]),
        "Acrylic": (acryl_xy[0], acryl_xy[1]),
        "Air": (air_xy[0], air_xy[1]),
        "Water": (water_xy[0], water_xy[1]),
    }

    roi_coords = SimpleNamespace(**dd)

    dfrows = {
        "Top Left": len(newvals[0]["xfiltered"]),
        "Top Right": len(newvals[1]["xfiltered"]),
        "Bottom Left": len(newvals[2]["xfiltered"]),
        "Bottom Right": len(newvals[3]["xfiltered"]),
        "Average (mm)": newvals[-1]["avg"],
        "Nominal (mm)": float(slice_thickness),
        "Avg difference from nominal (mm)": newvals[-1]["avg"] - float(slice_thickness),
    }
    barsdf_ = pd.DataFrame.from_dict(dfrows, orient="index")
    barsdf_.columns = ["No. Bars Counted"]
    barsdf = barsdf_.copy()
    barsdf_ = barsdf_.style.format("{:.2f}").hide(
        subset=None, level=None, names=False, axis=1
    )
    display(Markdown("### Bar Count Results:"))
    display(barsdf_)
    display(Markdown('<p style="page-break-before: always"></p>'))
    dftable = build_table(barsdf, "blue_light", index=True)
    pixels = adjpx.copy()
    roi_area = 200
    roi_radius_mm = np.sqrt(roi_area / np.pi)
    roi_radius_px = int(roi_radius_mm / px_width)
    masks = []
    display_img = pixels.copy()
    limits = {
        "Polyethylene": (-107, -84),
        "Water": (-7, 7),
        "Acrylic": (110, 135),
        "Bone": (850, 970),
        "Air": (-1005, -970),
    }
    final_values = []
    fig, ax = plt.subplots(figsize=(10, 10))
    for item in roi_coords.__dict__:
        material = item
        center = roi_coords.__dict__[item]
        blank = np.zeros(pixels.shape, dtype="uint8")
        cv2.circle(
            blank,
            center=roi_coords.__dict__[item],
            radius=roi_radius_px,
            color=(255),
            thickness=-1,
        )
        ax.add_patch(
            Circle(
                xy=center,
                radius=roi_radius_px,
                color="lightblue",
                fill=False,
                linewidth=2,
            )
        )
        masked = cv2.bitwise_and(pixels, pixels, mask=blank)
        copy = masked.copy()
        copy = copy[np.nonzero(copy)]
        mean = round(np.mean(copy), 2)
        std = round(np.std(copy), 2)
        text = f"{item}\nMean: {mean:.2f}\nStd: {std:.2f}"
        y0, dy = center[1], 14
        for i, line in enumerate(text.split("\n")):
            y = y0 + i * dy
            ax.text(
                x=center[0] + roi_radius_px * 2,
                y=y,
                s=line,
                color="lightblue",
                fontweight="bold",
                fontsize="large",
            )
            # cv2.putText(display_img, line, (center[0]+(2*roi_radius_px), y ), cv2.FONT_HERSHEY_SIMPLEX, 0.35,color=(100,100,100))
        itm = (item, mean, std, limits[material][0], limits[material][1])
        final_values.append(itm)
    ax.imshow(display_img, cmap="gray", vmin=-200, vmax=200)
    ax.axis("Off")

    mod1img3 = encode_figure(fig)
    plt.show()

    cols = [
        "Mean (HU)",
        "Std Dev (HU)",
        "ACR lower limit",
        "ACR Upper Limit",
        "Evaluation",
    ]
    indices = []
    entries = []
    for item in final_values:
        mean = item[1]
        lower = item[3]
        upper = item[4]
        eval = ""
        if mean >= lower and mean <= upper:
            eval = "Within Limits"
        if mean < lower:
            diff = lower - mean
            eval = f"Out of limit by {diff:.1f} HU"
        if mean > upper:
            diff = mean - upper
            eval = f"Out of limit by {diff:.1f} HU"
        newItem = [item[1], item[2], item[3], item[4], eval]
        indices.append(item[0])
        entries.append(newItem)
    ctdf_ = pd.DataFrame(entries)
    ctdf_.columns = cols
    ctdf_.index = indices
    ctdf = ctdf_.copy()
    ctdftable = build_table(ctdf, "blue_light", index=True)
    ctdf_ = (
        ctdf_.style.set_properties(**{"text-align": "center"})
        .format({"Mean (HU)": "{:.1f}", "Std Dev (HU)": "{:.1f}"})
        .set_table_styles([dict(selector="th", props=[("text-align", "center")])])
    )
    display(ctdf_)

    template = Template(
        """
    <h4 style='page-break-after: avoid;'>Slice Thickness</h4>
    <p>Line profiles are drawn across the slice thickness bar patterns. Bars with signal >50% above background are counted.</p>
    <div display="flex" flex-direction="row" max-width="1000px">
    <img src="{{img1path}}" width="450px"></img>
    <img src="{{img2path}}" width="450px"></img>
    </div>
    {{dftable}}
    <hr style='page-break-after: always; width:1000px; margin-left:0px'></hr>
    <h4>Module 1: CT Number Measurements</h4>
    <img src="{{img3path}}" width='1000px'></img>
    {{ctdftable}}
    <hr style='page-break-after: always; width:1000px; margin-left:0px'></hr>
    """
    )

    rendered_html = template.render(
        text="Test Addition",
        img1path=mod1img1,
        img2path=mod1img2,
        img3path=mod1img3,
        slice_thickness=slice_thickness,
        dftable=dftable,
        ctdftable=ctdftable,
    )
    report_path = html_path
    with open(report_path, "a") as Func:
        Func.write(rendered_html)
        Func.close()

    return barsdf, ctdf


def process_slice_forty(slice_coords, html_path):
    """
    Analyzes slice 40 (Module 2 of ACR Gammex Phantom)

    Parameters
    ----------
    slice_dict : [{"slice": pydicom.dataset.FileDataset, "loc": float, "top": (int,int), "bot": (int,int)},...] -> should have 4 elements for modules 1-4
    report_directory : str -> path to reports directory

    Returns
    -------
    df : pandas.DataFrame -> CNR measurements
    """

    slice = slice_coords[1]["slice"]
    resc_int = slice.RescaleIntercept
    resc_slope = slice.RescaleSlope
    pixels = slice.pixel_array
    px_copy = pixels.copy()
    blur = cv2.GaussianBlur(pixels, ksize=(21, 21), sigmaX=cv2.BORDER_DEFAULT)
    mm_per_pixel = slice.PixelSpacing[0]
    roi_radius_mm = np.sqrt(100 / np.pi)
    roi_radius = roi_radius_mm * 1 / mm_per_pixel
    rod_roi_radius = roi_radius * 0.6
    topx, topy = slice_coords[1]["top"]
    botx, boty = slice_coords[1]["bottom"]
    midx, midy = ((boty + topy) / 2, (botx + topx) / 2)
    midpoint = (int(midx), int(midy))
    md = np.sqrt((topx - midx) ** 2 + (topy - midy) ** 2)

    display(Markdown("### Module 2 Visual Analysis"))
    plt.figure(figsize=(10, 10))
    plt.axis("Off")
    plt.imshow(
        pixels,
        cmap="gray",
        vmin=(50 - resc_int) / resc_slope,
        vmax=(150 - resc_int) / resc_slope,
    )
    plt.show()
    display(Markdown("Diameter of smallest rods visible (mm): _______"))

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.axis("Off")
    ax.imshow(
        px_copy,
        cmap="gray",
        vmin=(50 - resc_int) / resc_slope,
        vmax=(150 - resc_int) / resc_slope,
    )
    mod2img1 = encode_figure(fig)

    # ax.plot((midx,topx),(midy,topy))
    xshift = topx - midx
    adjacent = np.sqrt((md**2) - (xshift**2))
    rot_angle = np.arctan(xshift / adjacent)
    # testr, testtheta = (0.54*md,rot_angle - radians(60))
    # testx,testy = xy_from_polar(testr,testtheta,midpoint)
    bigr, bigtheta = (0.58 * md, rot_angle)
    bigx, bigy = xy_from_polar(bigr, bigtheta, midpoint)
    bkgr, bkgtheta = (0.54 * md, rot_angle - (0.42))
    bkgx, bkgy = xy_from_polar(bkgr, bkgtheta, midpoint)
    aar, aatheta = (0.56 * md, rot_angle - (0.76))
    aax, aay = xy_from_polar(aar, aatheta, midpoint)
    aa = aax, aay
    ddr, ddtheta = (0.545 * md, rot_angle - (1.4))
    ddx, ddy = xy_from_polar(ddr, ddtheta, midpoint)
    dd = ddx, ddy
    ad_dist = np.sqrt((aax - ddx) ** 2 + (ddy - aay) ** 2)
    ad_opp = ddy - aay
    ad_adj = aax - ddx
    adtheta = np.arctan(ad_opp / ad_adj)
    bbx, bby = (
        aax - int((ad_dist * np.cos(adtheta) / 3)),
        aay + int((ad_dist * np.sin(adtheta) / 3)),
    )
    ccx, ccy = (
        aax - int((ad_dist * np.cos(adtheta) * 2 / 3)),
        aay + int((ad_dist * np.sin(adtheta) * 2 / 3)),
    )

    eer, eetheta = (0.56 * md, rot_angle - (0.82) - radians(72))
    eex, eey = xy_from_polar(eer, eetheta, midpoint)
    ee = eex, eey
    hhr, hhtheta = (0.56 * md, rot_angle - (1.37) - radians(72))
    hhx, hhy = xy_from_polar(hhr, hhtheta, midpoint)
    hh = hhx, hhy
    eh_dist = np.sqrt((hhx - eex) ** 2 + (hhy - eey) ** 2)
    eh_opp = hhy - eey
    eh_adj = hhx - eex
    ehtheta = np.arctan(eh_opp / eh_adj)
    ffx, ffy = (
        int(eex + (eh_dist * np.cos(ehtheta) / 3)),
        eey + int((eh_dist * np.sin(ehtheta) / 3)),
    )
    ggx, ggy = (
        int(eex + (eh_dist * np.cos(ehtheta) * 2 / 3)),
        eey + int((eh_dist * np.sin(ehtheta) * 2 / 3)),
    )

    ax.add_patch(
        p=Circle(
            xy=(bigx, bigy),
            radius=roi_radius,
            fill=False,
            edgecolor="lightblue",
            linewidth=1.5,
        )
    )
    ax.add_patch(
        p=Circle(
            xy=(bkgx, bkgy),
            radius=roi_radius,
            fill=False,
            edgecolor="lightblue",
            linewidth=1.5,
        )
    )
    ax.add_patch(
        p=Circle(
            xy=(aax, aay),
            radius=rod_roi_radius,
            fill=False,
            edgecolor="lightblue",
            linewidth=1.5,
        )
    )
    ax.add_patch(
        p=Circle(
            xy=(bbx, bby),
            radius=rod_roi_radius,
            fill=False,
            edgecolor="lightblue",
            linewidth=1.5,
        )
    )
    ax.add_patch(
        p=Circle(
            xy=(ccx, ccy),
            radius=rod_roi_radius,
            fill=False,
            edgecolor="lightblue",
            linewidth=1.5,
        )
    )
    ax.add_patch(
        p=Circle(
            xy=(ddx, ddy),
            radius=rod_roi_radius,
            fill=False,
            edgecolor="lightblue",
            linewidth=1.5,
        )
    )
    ax.add_patch(
        p=Circle(
            xy=(eex, eey),
            radius=rod_roi_radius,
            fill=False,
            edgecolor="lightblue",
            linewidth=1.5,
        )
    )
    ax.add_patch(
        p=Circle(
            xy=(ffx, ffy),
            radius=rod_roi_radius,
            fill=False,
            edgecolor="lightblue",
            linewidth=1.5,
        )
    )
    ax.add_patch(
        p=Circle(
            xy=(ggx, ggy),
            radius=rod_roi_radius,
            fill=False,
            edgecolor="lightblue",
            linewidth=1.5,
        )
    )
    ax.add_patch(
        p=Circle(
            xy=(hhx, hhy),
            radius=rod_roi_radius,
            fill=False,
            edgecolor="lightblue",
            linewidth=1.5,
        )
    )
    plt.show()
    mod2img2 = encode_figure(fig)
    maskbig = np.uint8(np.zeros(pixels.shape))
    cv2.circle(maskbig, (bigx, bigy), int(roi_radius), color=(255), thickness=-1)
    big_masked = cv2.bitwise_and(src1=pixels, src2=pixels, mask=maskbig)
    maskbkg = np.uint8(np.zeros(pixels.shape))
    cv2.circle(maskbkg, (bkgx, bkgy), int(roi_radius), color=(255), thickness=-1)
    bkg_masked = cv2.bitwise_and(src1=pixels, src2=pixels, mask=maskbkg)
    maska = np.uint8(np.zeros(pixels.shape))
    cv2.circle(maska, (aax, aay), int(rod_roi_radius), color=(255), thickness=-1)
    cv2.circle(maska, (bbx, bby), int(rod_roi_radius), color=(255), thickness=-1)
    cv2.circle(maska, (ccx, ccy), int(rod_roi_radius), color=(255), thickness=-1)
    cv2.circle(maska, (ddx, ddy), int(rod_roi_radius), color=(255), thickness=-1)
    a_masked = cv2.bitwise_and(src1=pixels, src2=pixels, mask=maska)
    maske = np.uint8(np.zeros(pixels.shape))
    cv2.circle(maske, (eex, eey), int(rod_roi_radius), color=(255), thickness=-1)
    cv2.circle(maske, (ffx, ffy), int(rod_roi_radius), color=(255), thickness=-1)
    cv2.circle(maske, (ggx, ggy), int(rod_roi_radius), color=(255), thickness=-1)
    cv2.circle(maske, (hhx, hhy), int(rod_roi_radius), color=(255), thickness=-1)
    e_masked = cv2.bitwise_and(src1=pixels, src2=pixels, mask=maske)

    def get_roi_values(masked_img):
        copy = masked_img.copy()
        copy = copy[np.nonzero(copy)]
        mean = round(np.mean(copy) * resc_slope + resc_int, 2)
        std = round(np.std(copy), 2)
        return (mean, std)

    bkgvals = get_roi_values(bkg_masked)
    bigvals = get_roi_values(big_masked)
    avals = get_roi_values(a_masked)
    evals = get_roi_values(e_masked)

    cnr = (bigvals[0] - bkgvals[0]) / bkgvals[1]
    acnr = (avals[0] - bkgvals[0]) / bkgvals[1]
    ecnr = (evals[0] - bkgvals[0]) / bkgvals[1]
    cols = ["Mean (HU)", "Std Dev (HU)", "Bkg Mean (HU)", "Bkg Std Dev (HU)", "CNR"]
    indices = ["25mm Rod", "6mm Rods", "5mm Rods"]
    entries = [
        [bigvals[0], bigvals[1], bkgvals[0], bkgvals[1], "{0:.2f}".format(cnr)],
        [avals[0], avals[1], bkgvals[0], bkgvals[1], "{0:.2f}".format(acnr)],
        [evals[0], evals[1], bkgvals[0], bkgvals[1], "{0:.2f}".format(ecnr)],
    ]
    cnrdf = pd.DataFrame(entries)
    cnrdf.columns = cols
    cnrdf.index = indices
    cnrcopy = cnrdf.copy()
    cnrdf = (
        cnrdf.style.set_properties(**{"text-align": "center"})
        .format(
            {
                "Mean (HU)": "{:.2f}",
                "Std Dev (HU)": "{:.2f}",
                "Bkg Mean (HU)": "{:.2f}",
                "Bkg Std Dev (HU)": "{:.2f}",
            },
        )
        .set_table_styles([dict(selector="th", props=[("text-align", "center")])])
    )
    Markdown("#### Module 2 ROI Analysis")
    display(cnrdf)
    cnrtable = build_table(cnrcopy, "blue_light", index=True)

    template = Template(
        """
    <h4>Module 2: Low Contrast Visual Evaluation</h4>
    <img width="1000px" src="{{mod2img1}}"></img>
    <p></p>
    <p>Diameter of Smallest Rods Visible (mm): ________ </p>
    <hr style='page-break-after: always; width:1000px; margin-left:0px'></hr>
    <h4 style='page-break-after: avoid;'>Module 2: Low Contrast ROI Analysis</h4>
    <p>ROI measurements are drawn for ACR CNR as well as a "group mean CNR" for the 6mm and 5mm rods.</p>
    <img width="1000px" src="{{mod2img2}}"></img>
    {{cnrtable}}
    <hr style='page-break-after: always; width:1000px; margin-left:0px'></hr>
    """
    )

    rendered_html = template.render(
        text="Test Addition", mod2img1=mod2img1, mod2img2=mod2img2, cnrtable=cnrtable
    )
    report_path = html_path
    with open(report_path, "a") as Func:
        Func.write(rendered_html)
        Func.close()
    return cnrcopy


def process_slice_eighty(slice_coords, html_path):
    """
    Analyzes slice 80 (Module 3 of ACR Gammex Phantom)

    Parameters
    ----------
    slice_dict : [{"slice": pydicom.dataset.FileDataset, "loc": float, "top": (int,int), "bot": (int,int)},...] -> should have 4 elements for modules 1-4
    report_directory : str -> path to reports directory

    Returns
    -------
    unifdf : pandas.DataFrame -> Uniformity measurements
    distdf : pandas.DataFrame -> Distance measurment
    """

    info80 = slice_coords[2]
    slice = info80["slice"]
    pixels = slice.pixel_array
    resc_int = slice.RescaleIntercept
    resc_slope = slice.RescaleSlope
    pixel_width = slice.PixelSpacing[0]

    fig1, ax1 = plt.subplots(figsize=(10, 10))
    ax1.axis("Off")
    ax1.imshow(pixels, cmap="gray", vmin=-50 - resc_int, vmax=50 - resc_int)
    plt.show()
    display(Markdown("### Artifact Evaluation Result: ______"))
    mod3img1 = encode_figure(fig1)

    roi_radius_mm = np.sqrt(400 / np.pi)
    roi_radius = int(roi_radius_mm / pixel_width)
    topx, topy = int(info80["top"][0]), int(info80["top"][1])
    botx, boty = int(info80["bottom"][0]), int(info80["bottom"][1])
    midpoint, phantom_radius, rot_angle = get_midpoint_and_rotation(
        (topx, topy), (botx, boty)
    )
    midx, midy = midpoint
    roi_distance = phantom_radius - 2 * roi_radius
    aa = (roi_distance, rot_angle + radians(90))
    bb = (roi_distance, rot_angle + radians(180))
    cc = (roi_distance, rot_angle + radians(270))
    dd = (roi_distance, rot_angle)
    polars = [aa, bb, cc, dd]
    xys = [
        midpoint,
    ]
    for item in polars:
        xy = xy_from_polar(item[0], item[1], midpoint)
        xys.append(xy)

    fig2, ax2 = plt.subplots(figsize=(10, 10))
    ax2.axis("Off")
    ax2.imshow(pixels, cmap="gray", vmin=-50 - resc_int, vmax=50 - resc_int)
    # centervals = get_circle_roi_values(pixels,(midx,midy),roi_radius,ax2,resc_int,resc_slope)
    vals_list = []
    for item in xys:
        vals = get_circle_roi_values(
            pixels, item, roi_radius, ax2, resc_int, resc_slope
        )
        vals_list.append(vals)
    plt.show()
    mod3img2 = encode_figure(fig2)
    center_mean = vals_list[0][0]
    diffs = []
    for item in vals_list:
        diff = item[0] - center_mean
        if np.abs(diff) <= 5:
            eval = "Pass"
        else:
            eval = "Fail"
        diffs.append((diff, eval))
    cols = ["Mean (HU)", "Difference (HU)", "Evaluation"]
    indices = ["Center", "3:00", "6:00", "9:00", "12:00"]
    entries = []
    for idx, item in enumerate(vals_list):
        new = [item[0], round(diffs[idx][0], 2), diffs[idx][1]]
        entries.append(new)
    unifdf_ = create_df(entries, cols, indices)
    unifdf = pd.DataFrame(entries, index=indices, columns=cols)
    display(unifdf_[0])
    uniftable = unifdf_[1]
    fig3, ax3 = plt.subplots(figsize=(10, 10))

    ax3.imshow(pixels, cmap="gray", vmin=-50 - resc_int, vmax=50 - resc_int)
    distance_px = find_distance_bbs(
        slice, (midx, midy), int(phantom_radius * 0.5), ax3, resc_int, resc_slope
    )
    distance_mm = distance_px * pixel_width
    dist_err = abs(100 - distance_mm)
    if dist_err <= 1:
        dist_eval = "Pass"
    else:
        dist_eval = "Fail"
    plt.show()
    mod3img3 = encode_figure(fig3)
    cols2 = ("Measured (mm)", "Nominal (mm)", "Difference (mm)", "Evaluation")
    indices2 = ["Distance between BBs"]
    diststring = "{0:.1f}".format(distance_mm)
    errstring = "{0:.1f}".format(dist_err)
    entries2 = [(diststring, 100.0, errstring, dist_eval)]
    distdf = pd.DataFrame(entries2, index=indices2, columns=cols2)
    distdf_ = create_df(entries2, cols2, indices2, dec_places=1)
    display(distdf)
    disttable = distdf_[1]

    template = Template(
        """
    <h4>Module 3: Artifact Visual Evaluation</h4>
    <img width="1000px" src="{{mod3img1}}"></img>
    <p></p>
    <p>Arfifact Evaluation: _______________________ </p>
    <hr style='page-break-after: always; width:1000px; margin-left:0px'></hr>
    <h4 style='page-break-after: avoid;'>Module 3: Uniformity</h4>
    <img width="1000px" src="{{mod3img2}}"></img>
    {{uniftable}}
    <hr style='page-break-after: always; width:1000px; margin-left:0px'></hr>
    <h4 style='page-break-after: avoid;'>Module 3: Geometric Accuracy</h4>
    <img width="1000px" src="{{mod3img3}}"></img>
    {{disttable}}
    <hr style='page-break-after: always; width:1000px; margin-left:0px'></hr>
    """
    )

    rendered_html = template.render(
        text="Test Addition",
        mod3img1=mod3img1,
        mod3img2=mod3img2,
        mod3img3=mod3img3,
        disttable=disttable,
        uniftable=uniftable,
    )
    report_path = html_path
    with open(report_path, "a") as Func:
        Func.write(rendered_html)
        Func.close()

    return (
        unifdf,
        distdf,
    )


def process_slice_onetwenty(slice_coords, html_path):
    """
    Analyzes slice 120 (Module 4 of ACR Gammex Phantom)

    Parameters
    ----------
    slice_dict : [{"slice": pydicom.dataset.FileDataset, "loc": float, "top": (int,int), "bot": (int,int)},...] -> should have 4 elements for modules 1-4
    report_directory : str -> path to reports directory

    Returns
    -------
    unifdf : pandas.DataFrame -> Uniformity measurements
    distdf : pandas.DataFrame -> Distance measurment
    """

    info120 = slice_coords[3]
    pixels = info120["slice"].pixel_array
    resc_int = info120["slice"].RescaleIntercept
    resc_slope = info120["slice"].RescaleSlope
    adjpx = pixels * resc_slope + resc_int
    pixel_width = info120["slice"].PixelSpacing[0]
    series_desc = info120["slice"].SeriesDescription or "series"
    site = info120["slice"].InstitutionName or "site"
    studydate = info120["slice"].StudyDate or "studydate"
    lp_roi_radius = int(11 * 0.55 / pixel_width)
    topx, topy = int(info120["top"][0]), int(info120["top"][1])
    top = topx, topy
    botx, boty = int(info120["bottom"][0]), int(info120["bottom"][1])
    bot = botx, boty
    midpoint, phantom_radius, rot_angle = get_midpoint_and_rotation(top, bot)
    lineshift = int(phantom_radius * 0.04)
    midx, midy = midpoint
    display(Markdown("### Module 4 Visual Analysis"))
    fig0, ax0 = plt.subplots(figsize=(10, 10))
    ax0.axis("Off")
    ax0.imshow(pixels, cmap="gray", vmin=1050 - resc_int, vmax=1150 - resc_int)
    plt.show()
    mod4img1 = encode_figure(fig0)
    display(Markdown("Smallest Pattern Visible (lp/cm): _______"))
    display(Markdown('<p style="page-break-after: always"></p>'))

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.axis("Off")
    ax.imshow(pixels, cmap="gray", vmin=-200 - resc_int, vmax=200 - resc_int)
    angles = [45, 90, 135, 180, 225, 270, 315, 360]
    roistats = []
    profiles = []
    display(Markdown("#### Module 4 line / circle ROI analysis"))
    for idx, angle in enumerate(angles):
        polar = (0.705 * phantom_radius, rot_angle - radians(angle))
        pt = xy_from_polar(polar[0], polar[1], midpoint)
        linestart = (pt[0] - lineshift, pt[1] + lineshift)
        lineend = (pt[0] + lineshift, pt[1] - lineshift)

        plt.plot((linestart[0], lineend[0]), (linestart[1], lineend[1]), color="green")
        profile = profile_line(
            pixels, (linestart[1], linestart[0]), (lineend[1], lineend[0])
        )
        min = profile.min()
        max = profile.max()
        mod = max - min
        profiles.append((idx, profile))
        mask = np.uint8(np.zeros(pixels.shape))
        cv2.circle(mask, pt, lp_roi_radius, color=(255), thickness=-1)
        ax.add_patch(
            Circle(
                xy=pt,
                radius=lp_roi_radius,
                color="blue",
                fill=False,
                linewidth=1.5,
            )
        )
        masked = cv2.bitwise_and(src1=pixels, src2=pixels, mask=mask)
        masked = masked[np.nonzero(masked)]
        mean = np.mean(masked) + resc_int
        max = np.max(masked) + resc_int
        min = np.min(masked) + resc_int
        std = np.std(masked)
        mod = (max - min) / (max + min)
        roistats.append(
            (round(mean), round(max), round(min), round(std, 1), round(mod, 2), idx)
        )
    lps = (4, 5, 6, 7, 8, 9, 10, 12)
    xs = lps
    ys = [x[3] for x in roistats]
    mods = [x[4] for x in roistats]

    mod4img2 = encode_figure(fig)

    cols = [f"{x} lp/cm" for x in lps]
    values = [mods]
    indices = ["Modulation"]
    moddf = pd.DataFrame(data=values, columns=cols)
    moddf.index = ["Modulation"]
    modcopy = moddf.copy()
    moddf_ = create_df(values, cols, indices, dec_places=2)
    modtable = build_table(df=modcopy, color="blue_light", index=True)
    display(moddf_[0])
    plt.show()
    fig2, ax2 = plt.subplots(4, 2, sharey=True)
    fig2.set_size_inches(12, 8)
    fig2.text(0.04, 0.5, "CT Number (HU)", va="center", rotation="vertical")
    fig2.suptitle("Resolution Pattern Line Profiles")
    ax2 = ax2.flatten()
    linemods = []
    for idx, tuple in enumerate(profiles):
        profile = tuple[1]
        profile = profile * resc_slope + resc_int
        max = np.max(profile)
        min = np.min(profile)
        mod = np.abs(max - min) / (max + min)
        linemods.append(mod)
        ax2[idx].set_ylim(0, 2000)
        ax2[idx].plot(profile, "g")
        ax2[idx].set_xticks([])
        ax2[idx].set_title(f"{lps[idx]} lp/cm")
        ax2[idx].axhline(y=max, color="lightblue")
        ax2[idx].axhline(y=min, color="lightblue")
    mod4img3 = encode_figure(fig2)

    fig3, ax3 = plt.subplots(figsize=(12, 8))
    # plt.plot(xs,ys,color="blue")
    # plt.plot(xs,linemods,color="orange")
    ax3.plot(xs, mods, color="b")
    ax3.set_title(f"Circle ROI Modulation vs. Line Pair Frequency")
    ax3.set_ylabel("Modulation\n(max-min)/(max+min)")
    ax3.set_xlabel("Bar Pattern Line Pairs/cm")
    plt.show()
    mod4img4 = encode_figure(fig3)

    template = Template(
        """
    <h4>Module 4: Spatial Resolution Visual Assessment</h4>
    <img width="1000px" src="{{mod4img1}}"></img>
    <p></p>
    <p>Highest Spatial Frequency Visualized (lp/cm): __________ </p>
    <hr style='page-break-after: always; width:1000px; margin-left:0px'></hr>
    <h4 style='page-break-after: avoid;'>Module 4: Circle and Line ROI Placement</h4>
    <img width="1000px" src="{{mod4img2}}"></img>
    <hr style='page-break-after: always; width:1000px; margin-left:0px'></hr>
    <h4 style='page-break-after: avoid;'>Module 4: Line Profile and ROI Modulation Analysis</h4>
    {{modtable}}
    <img src="{{mod4img3}}" height="550px" style='margin-left:62px;'></img>
    <br></br>
    <img src="{{mod4img4}}" height="550px" style='margin-left:62px;'></img>
    """
    )

    rendered_html = template.render(
        text="Test Addition",
        mod4img1=mod4img1,
        mod4img2=mod4img2,
        mod4img3=mod4img3,
        mod4img4=mod4img4,
        modtable=modtable,
    )
    report_path = html_path
    with open(report_path, "a") as Func:
        Func.write(rendered_html)
        Func.close()

    return moddf


def get_distance(pt1, pt2):
    a = (pt1[0] - pt2[0]) ** 2
    b = (pt1[1] - pt2[1]) ** 2
    dist = np.sqrt(a + b)
    return dist


def get_circle_roi_values(pixels, center, radius, ax, resc_int=1, resc_slope=1):
    """
    Get statistics for a circular ROI placed on an image

    Parameters
    ----------
    pixels : ndarray -> 2D image array
    center : tuple[int,int] -> x,y center point of circle
    radius : int -> radius of circle in pixels
    ax : matplotlib.axes.Axes -> axis to add circle graphic patch to (i.e. fig, ax = plt.subplots())

    Returns
    -------
    returns a tuple of (mean, max, min, std).
    mean : float -> mean pixel value
    max : float -> max pixel value
    min : float -> minimum pixel value
    std : float -> std deviation pixel value
    """
    width = pixels.shape[0]
    mask = np.uint8(np.zeros(pixels.shape))
    cv2.circle(mask, center, radius, color=(255), thickness=-1)
    masked = cv2.bitwise_and(src1=pixels, src2=pixels, mask=mask)
    copy = pixels.copy()
    copy = copy[np.nonzero(masked)]
    mean = round(np.mean(copy) * resc_slope + resc_int, 2)
    max = round(np.max(copy) * resc_slope + resc_int, 2)
    min = round(np.min(copy) * resc_slope + resc_int, 2)
    std = round(np.std(copy))
    patch = Circle(
        xy=center, radius=radius, fill=False, color="lightblue", linewidth=1.5
    )
    ax.add_patch(patch)
    text = f"Mean: {mean:.2f}\nMax:{max:.2f}\nMin:{min:.2f}\nStd: {std:.2f}"
    y0, dy = center[1], 14
    for i, line in enumerate(text.split("\n")):
        y = y0 + i * dy
        if width - center[0] > 3 * radius:
            ax.text(
                center[0] + 1.2 * radius,
                y - 0.5 * radius,
                line,
                fontsize="large",
                color="lightblue",
                fontweight="bold",
            )
        else:
            ax.text(
                center[0] - radius,
                y - 3 * radius,
                line,
                fontsize="large",
                color="lightblue",
                fontweight="bold",
            )

    return mean, max, min, std


def get_midpoint_and_rotation(top, bottom):
    """
    Find midpoint and angle relative to vertical between two points

    Parameters
    ----------
    top : tuple[int,int] -> x,y coordinate of top point (i.e. top BB)
    bottom : tuple[int,int] -> x,y coordinate of bottom point

    Returns
    -------
    midpoint : tuple[int,int] -> x,y coordinate between top and bottom
    phantom_radius : phantom radius (half distance between top and bottom points)
    rot_angle : angle of rotation relative to vertical in radians
    """
    topx, topy = top[0], top[1]
    botx, boty = bottom[0], bottom[1]
    midx, midy = int((topx + botx) / 2), int((topy + boty) / 2)
    midpoint = midx, midy
    phantom_radius = get_distance((midx, midy), (topx, topy))
    xshift = topx - midx
    adjacent = np.sqrt((phantom_radius**2) - (xshift**2))
    rot_angle = np.arctan(xshift / adjacent)
    return midpoint, phantom_radius, rot_angle


def create_df(entries, cols, indices, dec_places=2):
    """
    Create pandas dataframe (actually a styler) with centered headers and data cells
    round floats to specified number of dec_places, also create html table
    Note this formatting will not transfer to output PDF,
    it will only be when displayed visible in the jupyter notebook cell output.

    Parameters
    ----------
    entries : data points
    cols : names of columns
    indices : names of rows
    dec_places : number of decimal places for rounding floats

    Returns
    -------
    df : pandas.io.formats.style.Styler
    htmltable : dataframe converted to HTML table
    """
    df = pd.DataFrame(entries)
    df.columns = cols
    df.index = indices
    htmltable = build_table(df, "blue_light")
    formats = {}
    for idx, item in enumerate(cols):
        # if re.match(r'^-?\d+(?:\.\d+)$', entries[0][idx]) is not None:
        if not isinstance(entries[0][idx], str):
            formats[item] = f"{{:.{dec_places}f}}"
    df = (
        df.style.set_properties(**{"text-align": "center"})
        .format(formats)
        .set_table_styles([dict(selector="th", props=[("text-align", "center")])])
    )
    return df, htmltable


def find_distance_bbs(
    slice, center, radius, ax, resc_int, resc_slope, show_circle=False
):
    """
    Uses a central ROI mask to find the maximum pixel location of the top distance BB
    and an outer ROI mask to find max pixel location for the bottom BB at
    slice 80 (Module 3). Then measures distance between the two.

    Parameters
    ----------
    slice : pydicom.dataset.FileDataset -> slice to be searched for BBs
    center : center point x,y coordinate for central ROI
    radius : radius of central ROI in pixels
    ax : matplotlib.axes.Axes -> figure axis to add circle graphic patch to
    resc_int : rescale intercept for pixel values
    resc_slope : rescale slope for pixel values
    show_circle : bool, show ROI graphics (optional)

    Returns
    -------
    dist : float -> distance between diagonal BBs in same units as image PixelSpacing

    """
    pixels = slice.pixel_array
    pixel_spacing = slice.PixelSpacing[0]
    mask = np.uint8(np.zeros(pixels.shape))
    cv2.circle(mask, center, int(radius), color=(255), thickness=-1)
    masked = cv2.bitwise_and(src1=pixels, src2=pixels, mask=mask)
    # ax.imshow(masked,cmap="gray",vmin=-50-resc_int, vmax=50-resc_int)
    max_int = np.unravel_index(np.argmax(masked), masked.shape)

    # if show_circle:
    # ax.add_patch(Circle(center,int(radius),fill=False,color="lightblue",linewidth=1.5))
    pmask = np.uint8(np.zeros(pixels.shape))
    cv2.circle(pmask, center, int(radius * 2), color=(255), thickness=-1)
    pmasked = cv2.bitwise_and(pixels, pixels, mask=pmask)
    out_mask = cv2.bitwise_not(mask)
    outside_masked = cv2.bitwise_and(src1=pmasked, src2=pmasked, mask=out_mask)
    # ax.imshow(outside_masked,cmap="gray",vmin=-50-resc_int, vmax=50-resc_int)
    max_ext = np.unravel_index(np.argmax(outside_masked), outside_masked.shape)
    # ax.add_patch(Circle(center,int(radius*2),fill=False,color="green",linewidth=1.5))
    # ax.plot(max_ext[1],max_ext[0],marker="o")
    # ax.plot(max_int[1],max_int[0],marker="o",color='g')
    midpoint, dist, rotation = get_midpoint_and_rotation(max_int, max_ext)
    ax.plot((max_int[1], max_ext[1]), (max_int[0], max_ext[0]), color="lightblue")
    ax.axis("Off")
    dist = get_distance(max_int, max_ext)
    plt.text(
        midpoint[1] + 20,
        midpoint[0],
        f"{round(dist*pixel_spacing,1)} mm",
        fontsize="large",
        color="lightblue",
        fontweight="bold",
    )
    return dist


def select_series(image_directory: str, series: list):
    """
    Uses an IPython display widget to display checkbox selections for available series

    Parameters
    ----------
    image_directory : str -> path of directory to search for image series
    series : list -> an empty array for storing series names outside of function
    """
    checkboxes = series
    style = {"description_width": "initial"}
    if len(os.listdir(image_directory)) != 0:
        for dir in sorted(os.listdir(image_directory)):
            checkbox = widgets.Checkbox(
                value=False, description=dir, layout=widgets.Layout(width="100%")
            )
            checkboxes.append(checkbox)
        # submit_button = widgets.Button(description='Process')

        output = widgets.Output()
        ui = widgets.VBox(children=checkboxes)
        display(Markdown("<h2>Select one or more series to process:</h2>"))
        display(Markdown("<hr></hr>"))
        display(ui, output)
        display(
            Markdown(
                "<h2>When selections have been made, proceed and run next cell.</h2>"
            )
        )
    else:
        print("No uploads found. Run this cell again after upload.")


def local_select_series(src_path: str, series: list):
    """
    Uses an IPython display widget to display checkbox selections for available series

    Parameters
    ----------
    image_directory : str -> path of directory to search for image series
    series : list -> an empty array for storing series names outside of function
    """
    checkboxes = series
    series_dirs = [
        dirpath
        for (dirpath, dirnames, filenames) in os.walk(src_path)
        if os.path.basename(dirpath).startswith("Series")
    ]
    if len(series_dirs) != 0:
        for dir in sorted(series_dirs):
            checkbox = widgets.Checkbox(
                value=False, description=dir, layout=widgets.Layout(width="100%")
            )
            checkboxes.append(checkbox)
        # submit_button = widgets.Button(description='Process')

        output = widgets.Output()
        ui = widgets.VBox(children=checkboxes)
        display(Markdown("<p>Select one or more series to process:</p>"))
        display(Markdown("<hr></hr>"))
        display(ui, output)
        display(
            Markdown(
                "<p>When selections have been made, proceed and run next cell.</p>"
            )
        )
    else:
        print("No folders labeled 'Series...' found in source directory...")


def process_images(image_directory: str, report_directory: str, series: list[str]):
    """
    Process ACR phantom images for series names found in `series` list. Calls `process_phantom()`
    for each series. Reports are generated in appropriate reports directories. Finally
    reports/pdf and reports/csv are archived in zip format at main directory.

    Parameters
    ---------
    image_directory: str -> path to extracted images directory (i.e. images/new/)
    report_directory: str -> path to reports directory
    series : list[str] -> list of strings corresponding to names of image series folders

    """
    for item in series:
        if item.value == True:
            seriespath = os.path.join(image_directory, item.description)
            slices = get_slices(seriespath)
            print("")
            slice_coords = get_slice_coordinates(slices)
            process_phantom(slice_coords, report_directory="./reports")
    pdfdir = os.path.join(report_directory, "pdf/")
    csvdir = os.path.join(report_directory, "csv/")
    shutil.make_archive("Reports-PDF", "zip", pdfdir)
    shutil.make_archive("Reports-CSV", "zip", csvdir)
    print("Finished processing all series. Refresh folders and check reports folder.")


def local_process_phantom(
    slice_dict,
    report_directory="reports",
    with_pdf=False,
    path_to_wkhtmltopdf="",
):
    """
    Processes ACR CT images and saves analysis reports in PDF and CSV format

    Parameters
    ----------
    slice_dict : [
        {\n
            "slice" : pydicom.dataset.FileDataset -> DICOM image slice\n
            "loc" : float -> SliceLocation \n
            "top" : tuple[int,int] -> top BB x,y coordinate \n
            "bot" : tuple[int,int] -> bottom BB x,y coordinate \n
        }
    ] -> list should contain 4 dict elements, one for each module of the ACR Phantom
    report_directory : str, path to reports directory

    """

    title, table, html_path = local_generate_first_page(
        slice_dict[0]["slice"], report_directory
    )
    barsdf, ctdf = process_slice_zero(slice_dict, html_path)
    cnrdf = process_slice_forty(slice_dict, html_path)
    unifdf, distdf = process_slice_eighty(slice_dict, html_path)
    moddf = process_slice_onetwenty(slice_dict, html_path)

    csvname = html_path.replace(".html", ".csv")
    csvpath = os.path.join(report_directory, csvname)

    csvlist = []
    lines = []
    table = table.to_csv(
        os.path.join(report_directory, "table.csv"), index=False, header=None
    )
    csvlist.append(os.path.join(report_directory, "table.csv"))
    barsdf = barsdf.to_csv(os.path.join(report_directory, "bars.csv"))
    csvlist.append(os.path.join(report_directory, "bars.csv"))
    ctdf = ctdf.to_csv(os.path.join(report_directory, "ctdf.csv"))
    csvlist.append(os.path.join(report_directory, "ctdf.csv"))
    cnrdf = cnrdf.to_csv(os.path.join(report_directory, "cnr.csv"))
    csvlist.append(os.path.join(report_directory, "cnr.csv"))
    unifdf = unifdf.to_csv(os.path.join(report_directory, "unif.csv"))
    csvlist.append(os.path.join(report_directory, "unif.csv"))
    distdf = distdf.to_csv(os.path.join(report_directory, "dist.csv"))
    csvlist.append(os.path.join(report_directory, "dist.csv"))
    moddf = moddf.to_csv(os.path.join(report_directory, "mod.csv"))
    csvlist.append(os.path.join(report_directory, "mod.csv"))
    for sheet in csvlist:
        lines.append("")
        with open(sheet, "r") as f:
            reader = csv.reader(f, delimiter="\t")
            for i, line in enumerate(reader):
                lines.append(line)
    # csvdir = os.path.join(report_directory, "csv")
    # if not os.path.exists(csvdir):
    #     os.mkdir(csvdir)
    # maindir = os.getcwd()
    # os.chdir(csvdir)
    with open(csvpath, "w+", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter="\t")
        for line in lines:
            writer.writerow(line)
    # os.chdir(maindir)
    for file in csvlist:
        os.remove(file)

    if with_pdf:
        pdfdir = os.path.join(report_directory, "pdf")
        if not os.path.exists(pdfdir):
            os.mkdir(pdfdir)
        for file in os.listdir(report_directory):
            if file.endswith(".pdf"):
                oldpath = os.path.join(report_directory, file)
                newpath = os.path.join(pdfdir, file)
                shutil.move(oldpath, newpath)


def local_process_images(
    report_directory: str, series: list[str], with_pdf=False, path_to_wkhtmltopdf=""
):
    """
    Process ACR phantom images for series names found in `series` list. Calls `process_phantom()`
    for each series. Reports are generated in appropriate reports directories. Finally
    reports/pdf and reports/csv are archived in zip format at main directory.

    Parameters
    ---------
    report_directory: str -> path to directory for placing reports
    series : list[str] -> list of strings corresponding to paths image series folders

    """
    # try:
    for item in series:
        if item.value == True:
            seriespath = item.description
            slices = get_slices(seriespath)
            slice_coords = get_slice_coordinates(slices)
            local_process_phantom(
                slice_coords,
                report_directory=report_directory,
                with_pdf=with_pdf,
                path_to_wkhtmltopdf=path_to_wkhtmltopdf,
            )
    # if with_pdf:
    #     pdfdir = os.path.join(report_directory, "pdf")
    #     shutil.make_archive("Reports-PDF", "zip", pdfdir)

    # csvdir = os.path.join(report_directory, "csv")
    # if not os.path.exists()
    # shutil.make_archive("Reports-CSV", "zip", csvdir)
    # htmldir = os.path.join(report_directory, "html")
    # shutil.make_archive("Reports-HTML", "zip", htmldir)
    # print("Finished processing all series. Check reports location...")
    # if with_pdf:
    #     #handle PDF
    #     pass
    # except:
    #     print(
    #         "something went wrong during processing... results may not be complete or available..."
    #     )


def process_single_series_folder(
    image_folder_path: str,
    report_directory: str,
    with_pdf=False,
    path_to_wkhtmltopdf="",
):
    """
    Process ACR phantom images for series names found in `series` list. Calls `process_phantom()`
    for each series. Reports are generated in appropriate reports directories. Finally
    reports/pdf and reports/csv are archived in zip format at main directory.

    Parameters
    ---------
    report_directory: str -> path to directory for placing reports
    series : list[str] -> list of strings corresponding to paths image series folders

    """
    try:
        seriespath = image_folder_path
        slices = get_slices(seriespath)
        slice_coords = get_slice_coordinates(slices)
        local_process_phantom(
            slice_coords,
            report_directory=report_directory,
            with_pdf=with_pdf,
            path_to_wkhtmltopdf=path_to_wkhtmltopdf,
        )
        # if with_pdf:
        #     pdfdir = os.path.join(report_directory, "pdf")
        #     shutil.make_archive("Reports-PDF", "zip", pdfdir)

        # csvdir = os.path.join(report_directory, "csv")
        # if not os.path.exists()
        # shutil.make_archive("Reports-CSV", "zip", csvdir)
        # htmldir = os.path.join(report_directory, "html")
        # shutil.make_archive("Reports-HTML", "zip", htmldir)
        # print("Finished processing all series. Check reports location...")
        # if with_pdf:
        #     #handle PDF
        #     pass
    except:
        print(
            "something went wrong during processing... results may not be complete or available..."
        )
