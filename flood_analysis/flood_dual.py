# -*- coding: utf-8 -*-
import pydicom
import numpy as np
from scipy.ndimage import convolve
from cv2 import rectangle
import matplotlib.pyplot as plt


def get_simple_unif(imgpath, width_factor=0.85, height_factor=0.5, show_plots=False):
    img = pydicom.dcmread(imgpath)
    date = img["StudyDate"].value
    station_name = img["StationName"].value
    if (
        len(img.pixel_array.shape) > 2
    ):  # if the DICOM file contains more than one image (flood head1 and flood head2)
        pixels1 = img.pixel_array[0, :, :]  # flood head 1
        pixels2 = img.pixel_array[1, :, :]  # flood head 2
    else:  # if only a single image array (flood head 1)
        pixels1 = img.pixel_array
    width = pixels1.shape[1]
    height = pixels1.shape[0]
    new_width = width_factor * width
    new_height = height_factor * height
    width_incr = (width - new_width) // 2
    height_incr = (height - new_height) // 2
    top, bot, left, right = (
        int(0 + width_incr),
        int(width - width_incr),
        int(0 + height_incr),
        int(height - height_incr),
    )
    if show_plots:
        imgcopy = pixels1.copy()
        rectangle(imgcopy, (top, left), (bot, right), 1, 1)
        plt.imshow(imgcopy)
        plt.show()
    cropped = pixels1[left:right, top:bot]
    if show_plots:
        plt.imshow(cropped)
        plt.plot()
    mean = cropped.flatten().mean()
    min = cropped.flatten().min()
    max = cropped.flatten().max()
    PIU_int = (max - min) * 100 / (max + min)
    # print(round(mean), round(max), round(min))
    # print("PIU_int:", round(PIU_int, 2), "%")
    return station_name, date, PIU_int


def get_simplest_unif(imgpath):
    img = pydicom.dcmread(imgpath)
    date = img["StudyDate"].value
    station_name = img["StationName"].value
    if (
        len(img.pixel_array.shape) > 2
    ):  # if the DICOM file contains more than one image (flood head1 and flood head2)
        pixels1 = img.pixel_array[0, :, :]  # flood head 1
        pixels2 = img.pixel_array[1, :, :]  # flood head 2
    else:  # if only a single image array (flood head 1)
        pixels1 = img.pixel_array

    pixels1 = pixels1[pixels1.nonzero()]
    mean = pixels1.mean()
    min = pixels1.min()
    max = pixels1.max()
    PIU_int = (max - min) * 100 / (max + min)
    # print(round(mean), round(max), round(min))
    # print("PIU_int:", round(PIU_int, 2), "%")
    return station_name, date, PIU_int


def get_uniformity_dual(
    imgpath,
    u_width_factor=0.90,
    u_height_factor=0.90,
    c_width_factor=0.75,
    c_height_factor=0.75,
    bins=0,
    kernel=[[1, 2, 1], [2, 4, 2], [1, 2, 1]],
    with_logs=True,
):
    path = imgpath
    img = pydicom.dcmread(path)  # read the image with pydicom
    if (
        len(img.pixel_array.shape) > 2
    ):  # if the DICOM file contains more than one image (flood head1 and flood head2)
        pixels1 = img.pixel_array[0, :, :]  # flood head 1
        pixels2 = img.pixel_array[1, :, :]  # flood head 2
    else:  # if only a single image array (flood head 1)
        pixels1 = img.pixel_array
    if hasattr(img, "PixelSpacing"):
        pixel_spacing = img["PixelSpacing"].value  # get pixel spacing from header
    else:
        print("pixel spacing attribute not present, defaulting to 1 mm")
        pixel_spacing = 1
    study_date = img["StudyDate"].value if hasattr(img, "StudyDate") else "StudyDate"
    station_name = (
        img["StationName"].value if hasattr(img, "StationName") else "StationName"
    )
    serial_number = (
        img["SerialNumber"].value if hasattr(img, "SerialNumber") else "SerialNumber"
    )
    collimator = (
        img["CollimatorGridName"].value
        if hasattr(img, "CollimatorGridName")
        else "CollimatorGridName"
    )

    px_width = pixel_spacing[0]
    px_height = pixel_spacing[1]
    if with_logs:
        print(f"pixel size (mm): {round(px_width,2)} x {round(px_height,2)}")

    # Images most likely need to be binned, as NEMA specifies a large pixel size

    if bins == 0:
        # Determine bin size based on NEMA target pixel size (6.4mm +/- 30%)
        # choose the larger bin_size if both are within 30% for better uniformity result
        target_px_size = 6.4
        floor_ = (
            6.4 // px_width
        )  # find how many times pixel fits into target pixel size
        lower = px_width * floor_
        lower_error = (target_px_size - lower) / target_px_size
        higher = (floor_ + 1) * px_width
        higher_error = (higher - target_px_size) / target_px_size
        if higher_error < 0.3:
            bin_size = floor_ + 1
            bpxsize = higher
            err = higher_error
        else:
            bin_size = floor_
            bpxsize = lower
            err = lower_error
        bin_size = int(bin_size)
        if with_logs:
            print(
                "lower option:", round(lower, 2), "mm", " error:", round(lower_error, 2)
            )
            print(
                "higher option:",
                round(higher, 2),
                "mm",
                "error:",
                round(higher_error, 2),
            )
            print(
                f"bin_size {round(bin_size)} will be used for binned pixel size of {np.round(bpxsize,2)}mm \npixel size is {round(err*100)}% off from NEMA target (limit 30%)"
            )

    else:
        bin_size = bins

    binned_pixel_size = round(bin_size * px_width, 2)
    matrix_size = pixels1.shape[0]

    # if the selected bin_size does not cleanly divide into the matrix dimension
    # padding will be used to increase the size of the matrix and allow the proper binning
    # this shouldn't be an issue for our purposes as we are adding zeros onto an edge that already contains zeros
    # zeros are then ignored in the subsequent steps.

    # find number of pixels to add for the proper matrix dimension
    addpixels = 0
    if matrix_size % bin_size != 0:  # if division has nonzero remainder
        for i in range(
            1, 15, 1
        ):  # step through values to find how many pixels needed for clean division
            if (matrix_size + i) % bin_size == 0:
                addpixels = i
                break

    for_processing = pixels1  # copy of image for further processing
    if with_logs:
        print("original matrix:", for_processing.shape)
    # if adding pixels is needed:
    if addpixels != 0:
        if addpixels % 2 != 0:  # if number to add is not even
            startpad = addpixels // 2
            endpad = (
                addpixels // 2
            ) + 1  # bottom and right side will get an extra row/column
        else:  # if number of pixels to add is even, equal numbers of rows and columns added on all four sides
            startpad = addpixels // 2
            endpad = addpixels // 2
        for_processing = np.pad(
            pixels1,
            ((startpad, endpad), (startpad, endpad)),
            "constant",
            constant_values=(0),
        )  # pad image with rows/columns of zeros

    # Rebin the image...
    matrix = for_processing  # pixel matrix to be rebinned
    new_shape = (bin_size, bin_size)

    if matrix.shape[0] % new_shape[0] != 0 or matrix.shape[1] % new_shape[1] != 0:
        raise ValueError("Incompatible shapes for rebinning")

    rows, cols = matrix.shape
    new_rows, new_cols = new_shape

    meanlist = []  # empty array for placing 3x3 mean calculated values

    # loop through large matrix, breaking it into 3x3 submatrices
    for i in range(0, rows, new_rows):
        for j in range(0, cols, new_cols):
            submatrix = matrix[
                i : i + new_rows, j : j + new_cols
            ]  # 3x3 submatrix to be binned
            nonz = np.count_nonzero(submatrix)  # count non-zero elements in submatrix
            mean = 0  # start with a mean of zero
            if nonz != 0:  # if there are any nonzero elements in the submatrix
                mean = (
                    submatrix.sum() / nonz
                )  # set mean equal to mean of nonzero elements
            meanlist.append(mean)  # add mean to array
    meanlist = np.array(meanlist)  # convert to numpy array, necessary

    # reshape flat array into the desired 2d shape
    # reshape(x, -1) will give appropriate number of columns for x rows...:
    binned_image = meanlist.reshape(int(rows / new_rows), -1)
    if with_logs:
        print("rebinned matrix:", binned_image.shape)
    fullsum = np.sum(binned_image)  # sum all pixel values
    nz_mean = fullsum / len(
        binned_image[binned_image != 0]
    )  # find mean of all nonzero elements
    binned_75 = np.where(
        binned_image > nz_mean
    )  # find indices where pixel value is greater than 75% of nonzero mean value
    # find extremes of the >75% region
    bottom = binned_75[0].max()
    right = binned_75[1].max()
    top = binned_75[0].min()
    left = binned_75[1].min()

    if with_logs:
        print("top", top, "bottom", bottom, "left", left, "right", right)
    # original FOV
    fullwidth = right - left
    fullheight = bottom - top
    # UFOV width and increment to subtract on each side
    u_width = u_width_factor * fullwidth
    u_width_increment = (fullwidth - u_width) / 2
    u_height = u_height_factor * fullheight
    u_height_increment = (fullheight - u_height) / 2
    # CFOV width and increment to subtract on each side
    c_width = c_width_factor * fullwidth
    c_width_increment = (fullwidth - c_width) / 2
    c_height = c_height_factor * fullheight
    c_height_increment = (fullheight - c_height) / 2
    # tuples containing edge pixel location for each side
    u_top, u_bot, u_left, u_right = (
        int(top + u_height_increment),
        int(bottom - u_height_increment),
        int(left + u_width_increment),
        int(right - u_width_increment),
    )
    c_top, c_bot, c_left, c_right = (
        int(top + c_height_increment),
        int(bottom - c_height_increment),
        int(left + c_width_increment),
        int(right - c_width_increment),
    )

    # trim regions outside area of interest
    uimg = binned_image[u_top:u_bot, u_left:u_right]
    cimg = binned_image[c_top:c_bot, c_left:c_right]

    NEMA_kernel = np.array(kernel)

    c_convolved = convolve(cimg, NEMA_kernel)
    c_convolved = c_convolved / 16  # normalize pixel values to sum of kernel weights

    mean_c = c_convolved.mean()
    max_c = c_convolved.max()
    min_c = c_convolved.min()
    PIU_c = (max_c - min_c) * 100 / (max_c + min_c)

    u_convolved = convolve(uimg, NEMA_kernel)
    u_convolved = u_convolved / 16  # normalize pixel values to sum of kernel weights

    mean_u = u_convolved.mean()
    max_u = u_convolved.max()
    min_u = u_convolved.min()
    PIU_u = (max_u - min_u) * 100 / (max_u + min_u)

    dict = {
        "study_date": study_date,
        "station_name": station_name,
        "serial_number": serial_number,
        "collimator": collimator,
        "pixel_original_mm": px_width,
        "bin_size": bin_size,
        "pixel_binned_mm": binned_pixel_size,
        "u_width_factor": round(u_width_factor, 2),
        "u_height_factor": round(u_height_factor, 2),
        "c_width_factor": round(c_width_factor, 2),
        "c_height_factor": round(c_height_factor, 2),
        "kernel": kernel,
        "UFOV_int": PIU_u,
        "CFOV_int": PIU_c,
    }

    return dict


# results = get_uniformity(imgpath=r"C:\Users\M305747\OneDrive - Mayo Clinic\MPC\medical-physics\NM\Flood Analysis\11-28_MCD_ADAC\IMAGES\IM00001")
# print(results)

# for i in np.arange(0.1,1,step=0.02):
#     result = get_uniformity(imgpath=r"C:\Users\M305747\OneDrive - Mayo Clinic\MPC\medical-physics\NM\Flood Analysis\11-28_MCD_ADAC\IMAGES\IM00001",c_width_factor=i,c_height_factor=i,with_logs=False)
#     print("c_factor:",round(i,2),"PIU_int:",result[0]["CFOV"]["PIU_int"])

# for i in np.arange(1, 10, step=1):
#     result = get_uniformity_dual(
#         imgpath=r"C:\Users\M305747\OneDrive - Mayo Clinic\MPC\medical-physics\NM\Flood Analysis\11-28_MCD_ADAC\IMAGES\IM00001",
#         bins=i,
#         with_logs=False,
#     )
#     print(
#         "bins:",
#         round(i),
#         ", pixel:",
#         round(result[2] * i, 2),
#         "mm",
#         ", PIU_int:",
#         result[0]["CFOV"]["PIU_int"],
#     )
