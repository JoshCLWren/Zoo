"""
This script scans each python file in the project and checks for unused imports. It then removes them.
"""


import os
import re
import sys
from typing import List, Tuple

import stdlib_check

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
print(PROJECT_PATH)
# start by installing the requirements
os.system("pip install -r requirements.txt")
print("Installed requirements")
# List of files to ignore
IGNORE_FILES = ["dependency_cleanup.py", "stdlib_check.py"]
print("Ignoring files: ", IGNORE_FILES)
# add .gitignore to ignore files
with open(os.path.join(PROJECT_PATH, ".gitignore")) as f:
    IGNORE_FILES.extend(f.read().splitlines())
print("Ignoring files: ", IGNORE_FILES)
# List of directories to ignore
IGNORE_DIRS = [".git", "venv", "images", ".idea"]
print("Ignoring directories: ", IGNORE_DIRS)
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
print(f"Found {len(python_files)} python files")
env_packages = []
# Create a new requirements.txt file with the current environment packages
os.system("pip freeze > requirements.txt")
print("Created temporary requirements.txt file")
# install the requirements
os.system("pip install -r requirements.txt")
print("Installed requirements")
with open(os.path.join(PROJECT_PATH, "requirements.txt")) as f:
    env_packages.extend(line.split("==")[0] for line in f)
print(f"Found and installed {len(env_packages)} packages")
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
print("temporarily installed packages have been uninstalled")
# scan each python file for import statements and add them to a list
import_blocks = []
dead_imports = []
for file in python_files:
    print(f"Scanning {file} for imports")
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
            print(f"found import: {line}")
        if "from" in line:
            line = line.split("from")[1]
            print(f"found from import: {line}")
        clean_imports.append(line)
    files_imports = list(set(clean_imports))
    print(f"Found {len(files_imports)} imports in {file}")
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
    print(f"Found {len(valid_imports)} valid imports in {file} after second scan")
    valid_imports = list(set(valid_imports))
    print(f"Of the {len(files_imports)} imports in {file}, {len(valid_imports)} are referenced in the file")
    if files_imports > valid_imports:
        print(f"There are unused imports in {file}")
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
print(f"Found {len(import_blocks)} used imports in all files")
dead_imports = list(set(dead_imports))
print(f"Found {len(dead_imports)} unused imports in all files")
python_std_libraries = stdlib_check.get_stdlib_modules()
c_libraries = stdlib_check.get_c_implemented_modules()
builtin_libraries = stdlib_check.get_builtin_modules()
skipped_libraries = python_std_libraries + [c_libraries] + [builtin_libraries]
skipped_libraries =  list(set(skipped_libraries))
possible_project_level_libraries = [file[:-3] for file in IGNORE_FILES]
skipped_libraries.extend(possible_project_level_libraries)
skipped_libraries = list(set(skipped_libraries))
final_import_blocks = [
    import_block
    for import_block in import_blocks
    if import_block not in skipped_libraries
]
print(f"After removing python standard libraries and project imports, {len(final_import_blocks)} imports remain")
# check dead_imports for any imports that are possible_project_level_libraries
final_dead_imports = []
for import_block in dead_imports:
    if import_block.split(" ")[1] not in possible_project_level_libraries:
        final_dead_imports.append(import_block)
    else:
        print(f"Removing {import_block} from dead imports as it appears to be a project level import")
# remove the import statements from the files
for file in python_files:
    print(f"Removing unused imports from {file}")
    with open(file) as f:
        lines = f.read().splitlines()
    with open(file, "w") as f:
        for line in lines:
            # check if the line is an import statement
            if line.startswith("import") or line.startswith("from"):
                # check if the line is in the dead_imports list remove if from the file
                if line in final_dead_imports:
                    print(f"Removing '{line}' from {file}")
                    f.write("\n")
                else:
                    f.write(f"{line}\n")
            else:
                f.write(f"{line}\n")
# create a requirements.txt file
with open(os.path.join(PROJECT_PATH, "requirements.txt"), "w") as f:
    print(f"Writing {len(final_import_blocks)} imports to requirements.txt")
    for import_block in final_import_blocks:
        print(f"Writing {import_block} to requirements.txt")
        f.write(f"{import_block}\n")

print("Installing requirements.txt")
os.system("pip install -r requirements.txt")


# blackify and isort the files
print("Running black and isort")
os.system("black .")
os.system("isort .")
