# process_ct_folder

A tool to process and analyze a single folder of ACR Gammex 464 CT phantom images.

## Install

Place ctfunctions.py and process_ct_folder.py in your preferred location for python scripts. Ensure that these two files are located in the same folder. 

Python and required package dependencies must be installed. See [Dependencies](#Dependencies) section. 

## Usage (windows)

Open a powershell or cmd window and navigate to the location of the saved python files:

```powershell
PS C:\> cd <path\to\python_scripts>
```

Run the program:

```powershell
PS C:\path\to\python_scripts> python process_ct_folder.py
```

The program will initialize and load ctfunctions.py. When this has completed, a file browser window will appear. Browse for the desired folder <images_folder> containing dicom images in the file browser window. A new folder called <images_folder_reports> will be created in the same folder where <images_folder> is located.

## Dependencies
The python code in this repository depends on a particular version of python and particular python packages being installed. Most people choose to use a package/environment management solution like Anaconda to handle this. The file 'environment.yml' is placed here in order to facilitate creating the correct environment with the correct packages for running this code. For a guide on getting setup with Anaconda, see [Getting Started with Anaconda and Python](#getting-started-with-anaconda-and-python)

## Getting Started with Anaconda and Python

To work with Anaconda in Windows:
Download and install from [https://www.anaconda.com/download](https://www.anaconda.com/download).
You'll want to add Anaconda to the system PATH variable when prompted. This allows the command line to recognize and run programs by name like 'conda' and 'python'.
Once Anaconda Navigator is installed, open it and then run the 'Anaconda Powershell Prompt' from the suite of applications.
You should see (base) followed by PS and the current working folder at the prompt. You are working in the base environment.
The environment.yml in this repository can be used to clone an environment with the correct python packages needed for running the .py files in this repository.

Create a new environment and choose a name for it, replacing <C:\path\to\environment.yml> with the file path to the file on your local system and replacing <new_environment_name> with your desired name for this environment (i.e. gammex_processing):

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
You should now be able to run python files with the python keyword:

```powershell
(new_environment_name) PS C:\> python <program_name.py>
```

To deactivate an environment:

```powershell
(new_environment_name) PS C:\> conda deactivate new_environment_name
(base) PS C:\>
```
