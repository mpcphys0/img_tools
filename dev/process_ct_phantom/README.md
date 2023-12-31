# process_phantom_image_folder

A Jupyter notebook for processing

## Install

Place organize_dicom.py in your preferred location for python scripts. See package dependencies in next section. Optionally, save image_processing_environment.yml for creating a python environment. For a guide on using Anaconda for environment management see [Getting Started with Anaconda and Python](#getting-started-with-anaconda-and-python)

## Dependencies

pydicom >= 2.4.3

## Usage (windows)

Open a powershell or cmd window and run the .py file

```powershell
PS C:\path_to_python_script> python compare_dicom_gui.py
```

Browse for the desired folder <folder_to_organize> containing dicom images in the file browser window that pops up.
A new folder called <folder_to_organize_organized> will be created in the same directory where <folder_to_organize> is located.

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
