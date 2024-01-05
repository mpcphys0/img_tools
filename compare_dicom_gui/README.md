# compare_dicom

A simple GUI file select tool to compare the dicom header of two files side-by-side

## Install

Save a copy of compare_dicom.py in your preferred local folder for python scripts (i.e. C:\python_scripts). Required packages are shown in next section.

Optionally, save image_processing_environment.yml for creating an Anaconda python environment. For a guide on using Anaconda for environment management see [Getting Started with Anaconda and Python](#getting-started-with-anaconda-and-python)

## Dependencies

pandas >= 2.1.4
pydicom >= 2.4.3

## Usage (windows)

Place two to four dicom files to be compared into same directory. Open a powershell or cmd window and run the .py file (replacing <path-to-compare_dicom.py> with the full file path to where compare_dicom.py is saved):

```powershell
PS C:\> python <path-to-compare_dicom.py> 
```

Select the files to be compared in the file browser window that pops up. Comparison files (csv and HTML) will be generated in the directory where the image files are located

## Getting Started with Anaconda and Python

To work with Anaconda in Windows:
Download and install from [https://www.anaconda.com/download](https://www.anaconda.com/download).
Once Anaconda is installed, run the Anaconda Powershell Prompt from the suite of applications.
You should see (base) followed by PS and the current working directory at the prompt. You are working in the base environment.
The environment.yml can be used to clone an environment with a particular set of python installation and packages:

```powershell
(base) PS C:\> conda env create -f <path\to\environment.yml> -n <new_environment_name>
```

Show available environments:

```powershell
(base) PS C:\> conda env list
```

Activate the newly created environment:

```powershell
(base) PS C:\> conda activate new_environment_name
(new_environment_name) PS C:\>
```

Once the environment is activated, python scripts now have access to whichever version of Python is installed in that environment and also packages/libraries that have been installed.

Show packages installed in current working environment:

```powershell
(new_environment_name) PS C:\> conda list
```

To deactivate an environment:

```powershell
(new_environment_name) PS C:\> conda deactivate new_environment_name
(base) PS C:\>
```
