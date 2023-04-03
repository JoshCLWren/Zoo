"""
This script scans each python file in the project and checks for unused imports. It then removes them.
"""



import os
import re
import sys
from typing import List, Tuple

# Path to the project directory
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# List of files to ignore
IGNORE_FILES = ["dependency_cleanup.py"]

# add .gitignore to ignore files
with open(os.path.join(PROJECT_PATH, ".gitignore")) as f:
    IGNORE_FILES.extend(f.read().splitlines())

# List of directories to ignore
IGNORE_DIRS = [".git", "venv", "images"]

python_files = []

# Walk through the project directory and find all python files
for root, dirs, files in os.walk(PROJECT_PATH):
    # Remove ignored directories from the list
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
    for file in files:
        if file.endswith(".py") and file not in IGNORE_FILES:
            python_files.append(os.path.join(root, file))

env_packages = []
# Read the temp_requirements.txt file
with open(os.path.join(PROJECT_PATH, "requirements.txt")) as f:
    env_packages.extend(line.split("==")[0] for line in f)

# use pip to uninstall all packages
for package in env_packages:
    os.system(f"pip uninstall {package} -y")

# scan each python file for import statements and add them to a list
import_blocks = []
dead_imports = []
for file in python_files:
    files_imports = []
    valid_imports = []
    with open(file) as f:
        # read the file and split it into lines
        lines = f.read().splitlines()
        # find all import statements
        files_imports.extend([line for line in lines if line.startswith("import") or line.startswith("from")])
    # scan file again and look for references to the imported packages
    with open(file) as f:
        lines = f.read().splitlines()
        for line in lines:
            # check if the line contains a reference to an imported package
            valid_imports.extend(
                import_block
                for import_block in files_imports
                if import_block.split(" ")[1] in line
            )
    files_imports = list(set(files_imports))
    valid_imports = list(set(valid_imports))
    if files_imports > valid_imports:
        # if there are unused imports, add them to the dead_imports list
        dead_imports.extend([import_block for import_block in files_imports if import_block not in valid_imports])

    import_blocks.extend(valid_imports)
# remove duplicates
import_blocks = list(set(import_blocks))
dead_imports = list(set(dead_imports))

# remove the import statements from the files
for file in python_files:
    with open(file) as f:
        lines = f.read().splitlines()
    with open(file, "w") as f:
        for line in lines:
            # check if the line is an import statement
            if line.startswith("import") or line.startswith("from"):
                # check if the line is in the dead_imports list remove if from the file
                if line in dead_imports:
                    print(f"Removing {line} from {file}")
                    f.write("")
                else:
                    f.write(line)
            else:
                f.write(line)

# install the packages again
for package in env_packages:
    os.system(f"pip install {package}")

# create a requirements.txt file
os.system("pip freeze > requirements.txt")
# blackify and isort the files
os.system("black .")
os.system("isort .")