# process_ct_folder

A tool to process and analyze a single folder of ACR Gammex 464 CT phantom images.

## Install

Place ctfunctions.py and process_ct_folder.py in your preferred location for python scripts. Ensure that these two files are located in the same folder. See package dependencies in next section. 

## Dependencies

Refer to environment.yml. Optionally, save image_processing_environment.yml for creating an anaconda environment. For a guide on using Anaconda for environment management see [Getting Started with Anaconda and Python](#getting-started-with-anaconda-and-python)

## Usage (windows)

Open a powershell or cmd window and run the .py file. You'll need a functioning python installation and the file path to the location of process_ct_folder.py.

```powershell
PS C:\path_to_python_script> python process_ct_folder.py
```

The program will initialize and load ctfunctions.py. When this has completed, a file browser window will appear. Browse for the desired folder <images_folder> containing dicom images in the file browser window. A new folder called <images_folder_reports> will be created in the same folder where <images_folder> is located.

## Getting Started with Anaconda and Python

To work with Anaconda in Windows:
Download and install from [https://www.anaconda.com/download](https://www.anaconda.com/download).
Once Anaconda is installed, run the Anaconda Powershell Prompt from the suite of applications.
You should see (base) followed by PS and the current working folder at the prompt. You are working in the base environment.
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
