"""
This script scans each python file in the project and checks for unused imports. It then removes them.
"""

import os
import re
import sys
import time
import xmlrpc.client
from typing import List, Tuple

import stdlib_check


def main():
    """
    Main function.
    """

    base_requirements = BaseRequirements(default=True)
    project = Project()
    project.get_python_files()
    project.get_env_packages(base_requirements.base_requirements)
    project.get_imports()
    project.filter_imports()
    project.finalize()
    base_requirements.install()
    project.validate_requirements()
    project.cleanup()


class BaseRequirements:
    """
    Handles the base requirements for the project.
    """

    base_requirements = (
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
        "click",
        "typing-extensions",
        "astroid",
        "dill",
        "mccabe",
        "tomlkit",
    )

    def __init__(self, default):
        if default:
            self.base_requirements = self.base_requirements
        else:
            user_base_requirements = input(
                "Do you wish to use the standard base requirements? (y/n): "
            )
            if user_base_requirements != "y":
                self.base_requirements = None

    def install(self):
        if self.base_requirements:
            for dep in self.base_requirements:
                os.system(f"pip install {dep}")
        else:
            print("Skipping base requirements installation")


class Project:
    """
    Project level attributes and methods.
    """

    def __init__(self):
        self.PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
        print(self.PROJECT_PATH)
        # start by installing the requirements
        os.system("pip install -r requirements.txt")
        print("Installed requirements")
        # List of files to ignore
        self.IGNORE_FILES = ["dependency_cleanup.py", "stdlib_check.py"]
        print("Ignoring files: ", self.IGNORE_FILES)
        # add .gitignore to ignore files
        with open(os.path.join(self.PROJECT_PATH, ".gitignore")) as f:
            self.IGNORE_FILES.extend(f.read().splitlines())
        print("Ignoring files: ", self.IGNORE_FILES)
        # List of directories to ignore
        self.IGNORE_DIRS = [".git", "venv", "images", ".idea"]
        print("Ignoring directories: ", self.IGNORE_DIRS)
        self.python_files = []
        self.env_packages = []
        self.import_blocks = []
        self.dead_imports = []
        self.skipped_libraries = []
        self.possible_project_level_libraries = []
        self.final_import_blocks = []
        self.final_dead_imports = []
        self.top_level_python_files = []
        self.projects_modules = []

    def get_python_files(self):
        # Walk through the project directory and find all python files
        for root, dirs, files in os.walk(self.PROJECT_PATH):
            # Remove ignored directories from the list
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            self.python_files.extend(
                os.path.join(root, file)
                for file in files
                if file.endswith(".py") and file not in self.IGNORE_FILES
            )

        print(f"Found {len(self.python_files)} python files")

    def get_env_packages(self, base_requirements):
        # Create a new requirements.txt file with the current environment packages
        os.system("pip freeze > requirements.txt")
        print("Created temporary requirements.txt file")
        # install the requirements
        os.system("pip install -r requirements.txt")
        print("Installed requirements")
        with open(os.path.join(self.PROJECT_PATH, "requirements.txt")) as f:
            self.env_packages.extend(line.split("==")[0] for line in f)
        print(f"Found and installed {len(self.env_packages)} packages")
        # use pip to uninstall all packages
        for package in self.env_packages:
            if package not in (base_requirements):
                os.system(f"pip uninstall {package} -y")
        print("temporarily installed packages have been uninstalled")

    def get_imports(self):
        # scan each python file for import statements and add them to a list
        for file in self.python_files:
            python_file = PythonFile(file)
            print(f"Scanning {file} for imports")
            python_file.introspect()
            print(
                f"Found {len(python_file.files_imports)} imports in {python_file.file_location}"
            )
            self.import_blocks.extend(python_file.valid_imports)
            self.dead_imports.extend(python_file.dead_imports)
            python_file.remove_unused_imports(self.dead_imports)
        # remove duplicates
        self.import_blocks = list(set(self.import_blocks))
        print(f"Found {len(self.import_blocks)} used imports in all files")
        dead_imports = list(set(self.dead_imports))
        print(f"Found {len(dead_imports)} unused imports in all files")

    def filter_imports(self):
        python_std_libraries = stdlib_check.get_stdlib_modules()
        c_libraries = stdlib_check.get_c_implemented_modules()
        builtin_libraries = stdlib_check.get_builtin_modules()
        self.skipped_libraries = [
            lib for lib in c_libraries if lib in self.import_blocks
        ]
        self.skipped_libraries.extend(
            lib for lib in builtin_libraries if lib in self.import_blocks
        )
        self.skipped_libraries.extend(
            lib for lib in python_std_libraries if lib in self.import_blocks
        )
        print(f"Found {len(self.skipped_libraries)} python standard libraries")
        self.possible_project_level_libraries = [
            file[:-3] for file in self.IGNORE_FILES
        ]
        print(
            f"Found {len(self.possible_project_level_libraries)} possible project level libraries"
        )
        self.skipped_libraries.extend(self.possible_project_level_libraries)
        self.final_import_blocks = [
            import_block
            for import_block in self.import_blocks
            if import_block not in self.skipped_libraries
        ]
        print(
            f"After removing python standard libraries and project imports, {len(self.final_import_blocks)} imports remain"
        )
        # check dead_imports for any imports that are possible_project_level_libraries
        for import_block in self.dead_imports:
            if import_block.split(" ")[1] not in self.possible_project_level_libraries:
                self.final_dead_imports.append(import_block)
            else:
                print(
                    f"Removing {import_block} from dead imports as it appears to be a project level import"
                )

    def finalize(self):
        self.top_level_python_files = [
            file[:-3] for file in os.listdir(self.PROJECT_PATH) if file.endswith(".py")
        ]
        self.projects_modules = [
            folder for folder in os.listdir(self.PROJECT_PATH) if os.path.isdir(folder)
        ]
        self.final_import_blocks = list(set(self.final_import_blocks))

    def validate_requirements(self):
        self.final_import_blocks = list(set(self.final_import_blocks))
        for import_block in self.final_import_blocks:
            if "." in import_block:
                try:
                    import_block = import_block.split(".")[0]
                except Exception as e:
                    print(f"Failed to remove . from {import_block}: {e}")
                    continue
            if (
                import_block in self.top_level_python_files
                or import_block in self.projects_modules
            ):
                print(
                    f"Skipping {import_block} as it appears to be a project level import"
                )
                continue

            if _exists := self.package_exists_on_pypi(import_block):
                print(f"Adding {import_block} to environment")
                os.system(f"pip install {import_block}")

    def package_exists_on_pypi(self, package_name, retry_count=0):
        try:
            pypi = xmlrpc.client.ServerProxy("https://pypi.org/pypi")
            releases = pypi.package_releases(package_name)
            if len(releases) > 0:
                print(f"Package {package_name} exists on PyPI")
                return True
            else:
                print(f"Package {package_name} does not exist on PyPI")
                return False
        except Exception as e:
            print(
                f"Attempt {retry_count} failed to check if {package_name} exists on pypi: {e}, retrying..."
            )
            if "TooManyRequests" in e.faultString:
                e_list = e.faultString.split(" ")
                index_of_seconds = e_list.index("seconds.")
                seconds = int(e_list[index_of_seconds - 1])
                print(f"Sleeping for {seconds} seconds")
                time.sleep(seconds + 1)
            retry_count += 1
            if retry_count < 3:
                return self.package_exists_on_pypi(package_name, retry_count)

    @staticmethod
    def cleanup(lint=True):
        print("Compiling requirements.txt")
        os.system("pip install pip --upgrade")
        if lint:
            os.system("pip install black isort")
        os.system("pip freeze > requirements.txt")
        if lint:
            print("Running black and isort")
            os.system("black .")
            os.system("isort .")
        print("All done!")


class PythonFile:
    """
    A class to represent a python file
    """

    def __init__(self, file):
        self.files_imports = []
        self.valid_imports = []
        self.file_location = file
        self.lines = []
        self.clean_imports = []
        self.dead_imports = []

    def introspect(self):
        with open(self.file_location) as f:
            # read the file and split it into lines
            self.lines = f.read().splitlines()
            # find all import statements
            self.files_imports.extend(
                [
                    line
                    for line in self.lines
                    if line.startswith("import") or line.startswith("from")
                ]
            )
            # filter out "import" and from "import" statements

        for import_line in self.files_imports:
            if " " in import_line and "import" in import_line:
                # for import statements, remove the "import" part and keep the package name
                # for from import statements, remove the "from" part and keep the package name
                import_line = import_line.split(" ")[1]

            self.clean_imports.append(import_line)
        self.files_imports = list(set(self.clean_imports))
        # scan file again and look for references to the imported packages
        with open(self.file_location) as f:
            if not self.lines:
                self.lines = f.read().splitlines()
            for line in self.lines:
                # check if the line contains a reference to an imported package
                self.valid_imports.extend(
                    import_block
                    for import_block in self.files_imports
                    if import_block in line
                )
        self.files_imports = list(set(self.files_imports))
        print(
            f"Found {len(self.valid_imports)} valid imports in {self.files_imports} after second scan"
        )
        self.valid_imports = list(set(self.valid_imports))
        print(
            f"Of the {len(self.files_imports)} imports in {self.file_location}, {len(self.valid_imports)} are referenced in the file"
        )
        if self.files_imports > self.valid_imports:
            print(f"There are unused imports in {self.file_location}")
            # if there are unused imports, add them to the dead_imports list
            self.dead_imports.extend(
                [
                    import_block
                    for import_block in self.files_imports
                    if import_block not in self.valid_imports
                ]
            )

    def remove_unused_imports(self, final_dead_imports):
        print(f"Removing unused imports from {self.file_location}")
        if not self.lines:
            with open(self.file_location) as f:
                self.lines = f.read().splitlines()
        with open(self.file_location, "w") as f:
            for line in self.lines:
                # check if the line is an import statement
                if line.startswith("import") or line.startswith("from"):
                    # check if the line is in the dead_imports list remove if from the file
                    if line in final_dead_imports:
                        print(f"Removing '{line}' from {self.file_location}")
                        f.write("\n")
                    else:
                        f.write(f"{line}\n")
                else:
                    f.write(f"{line}\n")


if __name__ == "__main__":
    main()
