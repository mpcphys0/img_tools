# compare_dicom

A simple GUI file select tool to compare the dicom header of two files side-by-side

## Install

Save a copy of compare_dicom.py in your preferred local folder for python scripts (i.e. C:\python_scripts). Required packages are shown in next section.

Optionally, save image_processing_environment.yml for creating an Anaconda python environment. For a guide on using Anaconda for environment management see [Getting Started with Anaconda and Python](#getting-started-with-anaconda-and-python)

## Dependencies

```yml
pandas = "^2.1.4"
pydicom = "^2.4.3"
```
## Usage (windows)

Place two to four dicom files to be compared into same directory. Open a powershell or cmd window and run the .py file (replacing <path-to-compare_dicom.py> with the full file path to where compare_dicom.py is saved):

```powershell
C:\> python <path-to-compare_dicom.py> 
```

A file browser window will appear. Select 2 to 4 dicom files to compare. Comparison files (csv and HTML) will be generated in the directory where the image files are located

## Dependencies
The python code in this repository depends on a particular version of python and particular python packages being installed. Most people choose to use a package/environment management solution like Anaconda to handle this. The file 'environment.yml' is placed here in order to facilitate creating the correct environment with the correct packages for running this code. For a guide on getting setup with Anaconda, see below:
## Getting Started with Anaconda and Python

To work with Anaconda in Windows:
Download and install from [https://www.anaconda.com/download](https://www.anaconda.com/download).
You'll want to add Anaconda to the system PATH variable when prompted. You will need administrator priveleges. This allows the command line to recognize and run programs by name like 'conda' and 'python'. Once Anaconda Navigator is installed, open it and then run the 'Anaconda Powershell Prompt' from the suite of applications. You should see (base) followed by PS and the current working folder at the prompt. You are working in the base environment. The environment.yml in this repository can be used to clone an environment with the correct python packages needed for running the .py files in this repository.

Create a new environment and choose a name for it, replacing <path\to\environment.yml> with the file path to the file on your local system and replacing <new_environment_name> with your desired name for this environment (i.e. gammex_processing):

```powershell
conda env create -f path\to\environment.yml -n new_environment_name
```

Show available environments:

```powershell
conda env list
```

Activate the newly created environment:

```powershell
conda activate new_environment_name
```

Once the environment is activated, python scripts now have access to whichever version of Python is installed in that environment and also packages/libraries that have been installed.

Show packages installed in current working environment:

```powershell
conda list
```
You should now be able to run python files with the python keyword:

```powershell
python program_name.py
```

To deactivate an environment:

```powershell
conda deactivate new_environment_name
```
