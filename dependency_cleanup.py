"""
This script scans each python file in the project and checks for unused imports. It then removes them.
"""

import argparse
import ast
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
    parser = argparse.ArgumentParser(
        description="Clean up unused imports in a Python project."
    )
    parser.add_argument(
        "project_path",
        metavar="path",
        type=str,
        nargs="?",
        default=os.getcwd(),
        help="Path to the root of the project (default: current directory)",
    )

    args = parser.parse_args()

    project_path = os.path.abspath(args.project_path)

    base_requirements = BaseRequirements(default=True)
    project = Project(project_path=project_path)
    # project.install_requirements()
    project.get_python_files()
    # project.get_env_packages(base_requirements.base_requirements)
    project.get_imports()
    project.filter_imports()
    project.remove_dead_imports()
    project.finalize()
    # base_requirements.install()
    project.validate_requirements()
    project.cleanup()
    project.install_requirements(file="temp_requirements.txt")


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

    def __init__(self, project_path=None):
        self.PROJECT_PATH = project_path or os.path.dirname(os.path.abspath(__file__))
        print(self.PROJECT_PATH)
        # start by installing the requirements

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

    @staticmethod
    def install_requirements(file="requirements.txt"):
        # install the requirements
        os.system(f"pip install -r {file}")
        print("Installed requirements")

    def get_python_files(self):
        # Walk through the project directory and find all python files
        py_files = []
        for root, dirs, files in os.walk(self.PROJECT_PATH):
            # Remove ignored directories from the list
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            py_files.extend(
                os.path.join(root, file)
                for file in files
                if file.endswith(".py") and file not in self.IGNORE_FILES
            )
        # instantiate each python file as PythonFile object and add it to a list
        for file in py_files:
            self.python_files.append(PythonFile(file))
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
            if package not in base_requirements:
                os.system(f"pip uninstall {package} -y")
        print("temporarily installed packages have been uninstalled")

    def get_imports(self):
        # scan each python file for import statements and add them to a list
        for file in self.python_files:
            print(f"Scanning {file} for imports")
            file.introspect()
            print(f"Found {len(file.imports)} imports in {file.file_location}")
            self.import_blocks.extend(file.imports)

        # remove duplicates
        self.import_blocks = list(set(self.import_blocks))
        print(f"Found {len(self.import_blocks)} used imports in all files")
        self.dead_imports = list(set(self.dead_imports))
        print(f"Found {len(self.dead_imports)} unused imports in all files")

    def filter_imports(self):
        breakpoint()
        self.skipped_libraries = stdlib_check.Builtins().get(self.import_blocks)


        print(f"Found {len(self.skipped_libraries)} python standard libraries")
        self.possible_project_level_libraries = [
            file[:-3] for file in self.IGNORE_FILES
        ]
        print(
            f"Found {len(self.possible_project_level_libraries)} possible project level libraries"
        )
        self.skipped_libraries = list(set(self.skipped_libraries))
        self.skipped_libraries.extend(list(self.possible_project_level_libraries))
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

    def remove_dead_imports(self):
        for file in self.python_files:
            file.remove_unused_imports(self.final_dead_imports)

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
                print(f"Adding {import_block} to temporary requirements.txt file")
                with open("temp_requirements.txt", "a") as f:
                    f.write(f"{import_block}")

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
        print("Compiling new requirements.txt")
        if os.path.exists("temp_requirements.txt"):
            # overwrite requirements.txt with temp_requirements.txt
            print("Overwriting requirements.txt with temp_requirements.txt")
            os.system("mv temp_requirements.txt requirements.txt")
        else:
            os.system("pip freeze > requirements.txt")

        os.system("pip install pip --upgrade")
        if lint:
            os.system("pip install black isort")

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
        self.imports = []
        self.valid_imports = []
        self.file_location = file
        self.lines = []
        self.clean_imports = []
        self.dead_imports = []

    def introspect(self):
        with open(self.file_location, "r") as file:
            tree = ast.parse(file.read())

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if isinstance(node, ast.Import):
                        self.imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module
                        if module is not None:
                            self.imports.append(module)
        # now scan the file for usage of the imports and add them to valid_imports
        mutations_of_imports = []
        for import_ in self.imports:
            if "." in import_:
                mutations_of_imports.extend(
                    (import_.split(".")[0], import_.split(".")[1])
                )
        with open(self.file_location) as f:
            lines = f.read().splitlines()
        for line in lines:
            for partial_import in mutations_of_imports:
                if partial_import in line:
                    # find the import that matches this line
                    for full_import in self.imports:
                        if partial_import in full_import:
                            self.valid_imports.append(full_import)
                            break
        self.dead_imports = list(set(self.imports) - set(self.valid_imports))

    def remove_unused_imports(self, final_dead_imports):
        print(f"Removing unused imports from {self.file_location}")
        with open(self.file_location) as f:
            lines = f.read().splitlines()
        backup_lines = lines.copy()
        new_lines = []

        for node in ast.walk(ast.parse("\n".join(lines))):
            if isinstance(node, (ast.Import, ast.ImportFrom)) and (
                not new_lines or new_lines[-1] != lines[node.lineno - 1]
            ):
                new_lines.append(lines[node.lineno - 1])
        file_changes = False
        try:
            with open(self.file_location, "w") as f:
                for line in lines:
                    if line in final_dead_imports:
                        file_changes = True
                    if line not in final_dead_imports or line in new_lines:
                        f.write(f"{line}\n")
        except Exception as e:
            print(f"Failed to remove unused imports from {self.file_location}: {e}")
            with open(self.file_location, "w") as f:
                for line in backup_lines:
                    f.write(f"{line}\n")

        if file_changes:
            print(f"Removed unused imports from {self.file_location}")


if __name__ == "__main__":
    main()
