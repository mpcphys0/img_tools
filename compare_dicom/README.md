## Getting Started with Anaconda and Python

To work with Anaconda in Windows:
Download and install from [https://www.anaconda.com/download](https://www.anaconda.com/download)

Once Anaconda is installed, run the Anaconda Powershell Prompt application

You should see (base) followed by PS and the current working directory at the prompt. You are working in the base environment. The environment.yml can be used to clone an environment with a particular set of python installation and packages:

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

Once the environment is activate, python scripts now have access to whichever version of Python is installed in that environment and also packages/libraries that have been installed.

To deactivate an environment:

```powershell
(new_environment_name) PS C:\> conda deactivate new_environment_name
(base) PS C:\>
```
