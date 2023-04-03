"""
This script scans each python file in the project and checks for unused imports. It then removes them.
"""


import os
import re
import sys
from typing import List, Tuple

import stdlib_check

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

# start by installing the requirements
os.system("pip install -r requirements.txt")

# List of files to ignore
IGNORE_FILES = ["dependency_cleanup.py"]

# add .gitignore to ignore files
with open(os.path.join(PROJECT_PATH, ".gitignore")) as f:
    IGNORE_FILES.extend(f.read().splitlines())

# List of directories to ignore
IGNORE_DIRS = [".git", "venv", "images", ".idea"]

python_files = []

# Walk through the project directory and find all python files
for root, dirs, files in os.walk(PROJECT_PATH):
    # Remove ignored directories from the list
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
    python_files.extend(
        os.path.join(root, file)
        for file in files
        if file.endswith(".py") and file not in IGNORE_FILES
    )
env_packages = []
# Create a new requirements.txt file with the current environment packages
os.system("pip freeze > requirements.txt")
# install the requirements
os.system("pip install -r requirements.txt")
with open(os.path.join(PROJECT_PATH, "requirements.txt")) as f:
    env_packages.extend(line.split("==")[0] for line in f)

# use pip to uninstall all packages
for package in env_packages:
    if package not in (
        "pip",
        "setuptools",
        "wheel",
        "pdbpp",
        "black",
        "flake8",
        "isort",
        "pylint",
        "pydocstyle",
        "mypy",
        "fancycompleter",
    ):
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
        files_imports.extend(
            [
                line
                for line in lines
                if line.startswith("import") or line.startswith("from")
            ]
        )
    # filter out "import" and from "import" statements
    clean_imports = []
    for line in files_imports:
        if "import" in line:
            line = line.split("import")[1]
        if "from" in line:
            line = line.split("from")[1]
        clean_imports.append(line)
    files_imports = list(set(clean_imports))
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
        dead_imports.extend(
            [
                import_block
                for import_block in files_imports
                if import_block not in valid_imports
            ]
        )

    import_blocks.extend(valid_imports)
# remove duplicates
import_blocks = list(set(import_blocks))
dead_imports = list(set(dead_imports))

python_std_libraries = stdlib_check.get_stdlib_modules()
c_libraries = stdlib_check.get_c_implemented_modules()
builtin_libraries = stdlib_check.get_builtin_modules()
skipped_libraries = python_std_libraries + c_libraries + builtin_libraries
final_import_blocks = [
    import_block
    for import_block in import_blocks
    if import_block not in skipped_libraries
]
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
                    f.write(f"{line}\n")
            else:
                f.write(f"{line}\n")
# create a requirements.txt file
with open(os.path.join(PROJECT_PATH, "requirements.txt"), "w") as f:
    for import_block in final_import_blocks:
        f.write(f"{import_block}\n")


os.system("pip install -r requirements.txt")


# blackify and isort the files
os.system("black .")
os.system("isort .")
