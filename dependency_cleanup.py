"""
This script scans each python file in the project and checks for unused imports. It then removes them.
"""

import argparse
import ast
import os
import re
import subprocess
import sys
import time
import xmlrpc.client
from typing import List, Tuple

import stdlib_check
import logging
import argparse
import builtins
import logging
import sys

verbose_output = False


def custom_print(*args, **kwargs):
    if verbose_output:
        builtins.print(*args, **kwargs)


def install_pip(args):
    """
    Install pip if it is not found.
    """
    try:
        import pip
    except ImportError:
        custom_print("pip not found. Installing pip...")
        try:
            cmd = [sys.executable, "-m", "ensurepip", "--default-pip"]
            if args.silent:
                cmd.append("--quiet")
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            custom_print("Failed to install pip through ensurepip.")
            custom_print("Installing pip through get-pip.py...")
            try:
                install_pip_urllib(args)
            except Exception as e:
                custom_print(f"Failed to install pip. Error: {e}")
                sys.exit(1)


def install_pip_urllib(args):
    import urllib.request

    url = "https://bootstrap.pypa.io/get-pip.py"
    file_name = "get-pip.py"
    urllib.request.urlretrieve(url, file_name)
    cmd = [sys.executable, file_name]
    if args.silent:
        cmd.append("--quiet")
    subprocess.check_call(cmd)
    os.remove(file_name)
    custom_print("pip installed successfully.")


def main(args):
    """
    Main function.
    """
    project_path = args.project_path or os.getcwd()

    startup_log = "Starting dependency_cleanup..."
    global verbose_output
    verbose_output = verbose_output = not args.silent
    custom_print(startup_log)
    install_pip(args)
    requirements = Requirements(default=True)
    requirements.check_env_packages(args)

    project = Project(project_path=project_path)
    requirements.install(args, scan_project=True)
    project.get_python_files()
    project.get_imports()
    project.filter_imports(requirements)
    assert "PyDictionary" not in project.final_dead_imports
    project.remove_dead_imports()
    project.validate_requirements(requirements)
    requirements.remove_unused_requirements(args)
    requirements.install(args, scan_project=False)


class Requirements:
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
    txt_requirements = []
    requirements_installed = []
    temp_requirements_file = None
    packages_to_install = []
    backup_requirements = None
    packages_to_remove = []

    def __init__(self, default, project_path=None):
        self.PROJECT_PATH = project_path or os.getcwd()
        if default:
            self.base_requirements = self.base_requirements
        else:
            user_base_requirements = input(
                "Do you wish to use the standard base requirements? (y/n): "
            )
            if user_base_requirements != "y":
                self.base_requirements = None

    def remove_unused_requirements(self, args):
        """
        Remove any unused requirements from the environment.
        """
        if self.packages_to_remove:
            custom_print("Removing unused requirements...")
            removed_requirements = "removed_requirements.txt"
            with open(removed_requirements, "w") as f:
                for package in self.packages_to_remove:
                    if package in self.requirements_installed:
                        f.write(f"{package}\r")

            cmd = f"pip uninstall -r {removed_requirements} -y"
            if args.silent:
                cmd += " -q"
            os.system(cmd)
            os.remove(removed_requirements)

    def install(self, args, scan_project=False):
        """
        Install the base requirements for this project and compile a list of requirements.txt
        :return:
        """
        if not self.requirements_installed:
            self.check_env_packages()
        if self.packages_to_install:
            custom_print("Installing base requirements...")
            # create a temporary requirements file
            self.install_missing(args)
        self.create_requirements_file(scan_project=scan_project)

    def create_requirements_file(
            self, create_master_requirements=True, scan_project=True
    ):
        """
        Create a requirements.txt file for the project.
        :return:
        """
        # look for any .txt files in the project that contain requirements
        requirements_files = []
        if scan_project:
            for root, dirs, files in os.walk(self.PROJECT_PATH):
                requirements_files.extend(
                    os.path.join(root, file)
                    for file in files
                    if file.endswith(".txt") and "requirements" in file
                )
        elif os.path.exists("requirements.txt"):
            requirements_files = ["requirements.txt"]
        self.backup_requirements = os.path.join(
            self.PROJECT_PATH, "requirements_backup.txt"
        )
        with open(self.backup_requirements, "w") as f:
            # create a tmp requirement directory
            os.path.join(self.PROJECT_PATH, "tmp_requirements")
            # make a copy of each requirements file in the tmp directory
            for file in requirements_files:
                with open(file, "r") as f2:
                    for line in f2:
                        f.write(line)

        if create_master_requirements:
            self._master_txt_file_gen()

    def _master_txt_file_gen(self):
        # create a master requirements file
        if os.path.exists("requirements.txt"):
            os.remove("requirements.txt")
        if not isinstance(self.base_requirements, list):
            self.base_requirements = list(self.base_requirements)
        if not isinstance(self.requirements_installed, list):
            self.requirements_installed = list(self.requirements_installed)
        # combine the base requirements with the requirements installed in the environment and write to file
        # with no duplicates
        requirements_set = set(self.base_requirements + self.requirements_installed)
        # alphabetize the requirements regardless of case
        requirements_set = sorted(requirements_set, key=lambda s: s.lower())
        with open("requirements.txt", "w") as f:
            for package in requirements_set:
                f.write(f"{package}\r")

    def install_missing(self, args):
        """
        Install the missing packages.
        Creates a temporary requirements file and installs the packages from it.
        Does not install packages that are already installed.
        """
        self.temp_requirements_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "temp_requirements.txt"
        )
        with open(self.temp_requirements_file, "w") as f:
            for package in self.packages_to_install:
                f.write(f"{package}\r")
        cmd = f"{sys.executable} -m pip install -r {self.temp_requirements_file}"

        if args.silent:
            cmd += " -q"
        os.system(cmd)
        os.remove(self.temp_requirements_file)
        custom_print("Base requirements installed successfully.")

    def check_env_packages(self, args):
        cmd = [sys.executable, "-m", "pip", "freeze"]
        if args.silent:
            cmd.append("-q")
        env_packages = subprocess.check_output(cmd)
        env_packages = env_packages.decode("utf-8").splitlines()
        packages_to_install = []
        for package in env_packages:
            self.requirements_installed.append(package.split("==")[0])
        if self.base_requirements:
            for package in self.base_requirements:
                if package not in env_packages:
                    self.txt_requirements.append(package)
                    packages_to_install.append(package)
        if packages_to_install:
            self.packages_to_install = packages_to_install


class Project:
    """
    Project level attributes and methods.
    """

    def __init__(self, project_path=None, silent=False):
        self.PROJECT_PATH = project_path or os.path.dirname(os.path.abspath(__file__))
        custom_print(self.PROJECT_PATH)
        # start by installing the requirements

        custom_print("Installed requirements")
        # List of files to ignore
        self.IGNORE_FILES = ["dependency_cleanup.py", "stdlib_check.py"]
        custom_print("Ignoring files: ", self.IGNORE_FILES)
        # add .gitignore to ignore files
        with open(os.path.join(self.PROJECT_PATH, ".gitignore")) as f:
            self.IGNORE_FILES.extend(f.read().splitlines())
        custom_print("Ignoring files: ", self.IGNORE_FILES)
        # List of directories to ignore
        self.IGNORE_DIRS = [".git", "venv", "images", ".idea"]
        custom_print("Ignoring directories: ", self.IGNORE_DIRS)
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
        custom_print(f"Found {len(self.python_files)} python files")

    def get_imports(self):
        # scan each python file for import statements and add them to a list
        for file in self.python_files:
            custom_print(f"Scanning {file} for imports")
            file.introspect()
            custom_print(f"Found {len(file.imports)} imports in {file.file_location}")
            self.import_blocks.extend(file.imports)
            self.dead_imports.extend(file.dead_imports)

        # remove duplicates
        self.import_blocks = list(set(self.import_blocks))
        custom_print(f"Found {len(self.import_blocks)} used imports in all files")
        self.dead_imports = list(set(self.dead_imports))
        custom_print(f"Found {len(self.dead_imports)} unused imports in all files")

    def filter_imports(self, requirements_instance):
        assert "PyDictionary" not in self.final_dead_imports
        self.import_blocks = [
            import_block.split(".")[0] for import_block in self.import_blocks
        ]
        self.skipped_libraries = stdlib_check.Builtins().get(self.import_blocks)

        custom_print(f"Found {len(self.skipped_libraries)} python standard libraries")
        self.possible_project_level_libraries = [
            file[:-3] for file in self.IGNORE_FILES
        ]
        custom_print(
            f"Found {len(self.possible_project_level_libraries)} possible project level libraries"
        )
        self.skipped_libraries = list(set(self.skipped_libraries))
        self.skipped_libraries.extend(list(self.possible_project_level_libraries))
        self.final_import_blocks = [
            import_block
            for import_block in self.import_blocks
            if import_block not in self.skipped_libraries
        ]
        custom_print(
            f"After removing python standard libraries and project imports, {len(self.final_import_blocks)} imports remain"
        )
        assert "PyDictionary" not in self.final_dead_imports
        # check dead_imports for any imports that are possible_project_level_libraries
        for import_block in self.dead_imports:
            if (
                    " " in import_block
                    and import_block.split(" ")[1]
                    not in self.possible_project_level_libraries
            ):
                self.final_dead_imports.append(import_block)
            if import_block not in self.possible_project_level_libraries:
                self.final_dead_imports.append(import_block)
            else:
                custom_print(
                    f"Removing {import_block} from dead imports as it appears to be a project level import"
                )
        assert "PyDictionary" not in self.final_dead_imports
        assert "PyDictionary" not in self.final_dead_imports
        self.top_level_python_files = [
            file[:-3] for file in os.listdir(self.PROJECT_PATH) if file.endswith(".py")
        ]
        self.projects_modules = [
            folder for folder in os.listdir(self.PROJECT_PATH) if os.path.isdir(folder)
        ]
        self.final_import_blocks = list(set(self.final_import_blocks))

        self.final_import_blocks = [
            lib
            for lib in self.final_import_blocks
            if lib not in self.final_dead_imports
               and lib not in self.top_level_python_files
               and lib not in self.projects_modules
        ]
        assert "PyDictionary" not in self.final_dead_imports
        self.final_import_blocks = list(set(self.final_import_blocks))
        for import_block in self.final_dead_imports:
            requirements_instance.packages_to_remove.append(import_block)
        assert "PyDictionary" not in self.final_dead_imports

    def remove_dead_imports(self):
        assert "PyDictionary" not in self.final_dead_imports
        for file in self.python_files:
            file.remove_unused_imports(self.final_dead_imports)

    def validate_requirements(self, requirements_instance):
        self.final_import_blocks = list(set(self.final_import_blocks))
        for import_block in self.final_import_blocks:
            if "." in import_block:
                try:
                    import_block = import_block.split(".")[0]
                except Exception as e:
                    custom_print(f"Failed to remove . from {import_block}: {e}")
                    continue

            if package := self.package_exists_on_pypi(import_block):
                requirements_instance.packages_to_install.append(package)

    def package_exists_on_pypi(self, package_name, retry_count=0):
        pypi_package_aliases = {  # there are some packages that have changed names on pypi
            "PIL": "Pillow",  # Pillow is the new name for PIL
            "bs4": "beautifulsoup4",  # beautifulsoup4 is the new name for bs4
        }
        if package_name in pypi_package_aliases:
            self.import_blocks = [
                module for module in self.import_blocks if module != package_name
            ]
            package_name = pypi_package_aliases[package_name]
            self.import_blocks.append(package_name)
        try:
            pypi = xmlrpc.client.ServerProxy("https://pypi.org/pypi")
            releases = pypi.package_releases(package_name)
            if len(releases) > 0:
                custom_print(f"Package {package_name} exists on PyPI")
                return package_name
            else:
                custom_print(f"Package {package_name} does not exist on PyPI")
                return False
        except Exception as e:
            custom_print(
                f"Attempt {retry_count} failed to check if {package_name} exists on pypi: {e}, retrying..."
            )
            if "TooManyRequests" in e.faultString:
                e_list = e.faultString.split(" ")
                try:
                    index_of_seconds = e_list.index("seconds.")
                    seconds = int(e_list[index_of_seconds - 1])
                    custom_print(f"Sleeping for {seconds} seconds")
                    self.countdown(seconds)
                except ValueError:
                    custom_print("Failed to parse faultString, sleeping for 10 seconds")
                    self.countdown(11)
            retry_count += 1
            if retry_count < 3:
                return self.package_exists_on_pypi(package_name, retry_count)

    @staticmethod
    def countdown(seconds):
        seconds += 1
        for index, second in enumerate(range(seconds)):
            if index not in [0, 1]:
                # count down from seconds to 0
                custom_print("\033[F")
                custom_print(f"{seconds - index} seconds remaining")
                # clear the line above
            time.sleep(1)


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
        """
        Introspect the file and find all imports and separate them into valid and invalid imports
        valid imports are imports that are used in the file
        dead imports are imports that are not used in the file beyond the import statement
        :return:
        """
        with open(self.file_location, "r") as file:
            tree = ast.parse(file.read())

        imported_names = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if isinstance(node, ast.Import):
                        imported_name = alias.name
                    elif isinstance(node, ast.ImportFrom):
                        imported_name = alias.name if node.module is None else f"{node.module}.{alias.name}"
                    self.imports.append(imported_name)
                    imported_names.add(alias.name)

        class UsageVisitor(ast.NodeVisitor):
            def __init__(self, imported_names):
                self.imported_names = imported_names
                self.used_names = set()

            def visit_Name(self, node):
                if node.id in self.imported_names:
                    self.used_names.add(node.id)

        visitor = UsageVisitor(imported_names)
        visitor.visit(tree)

        self.valid_imports = list(visitor.used_names)

        # Consider an import valid if its root is in valid_imports
        def is_valid_import(import_):
            if "." not in import_:
                return import_ in self.valid_imports
            root = import_.split(".")[0]
            return root in self.valid_imports

        for import_ in self.imports:
            if is_valid_import(import_):
                self.valid_imports.append(import_)
            else:
                split_import = import_.split(".")
                index_one = split_import[0]
                try:
                    index_two = split_import[1]
                except IndexError:
                    index_two = None

                if is_valid_import(index_one) and index_one not in self.valid_imports:
                    self.valid_imports.append(index_one)
                    continue
                if not index_two:
                    self.dead_imports.extend([import_, index_one])
                    continue
                elif is_valid_import(index_two) and index_two not in self.valid_imports:
                    self.valid_imports.append(index_two)
                    continue
                else:
                    self.dead_imports.extend([import_, index_one, index_two])
        valid_import_copy = self.valid_imports.copy()
        for module in valid_import_copy:
            if "." in module:
                self.valid_imports.append(module.split(".")[0])
                self.valid_imports.append(module.split(".")[1])
                self.valid_imports.append(module)
        self.valid_imports = list(set(self.valid_imports))
        self.dead_imports = list(set(self.dead_imports))
        dead_import_copy = self.dead_imports.copy()
        # add any varations of imports to self.valid_imports i.e; 'bs4.BeautifulSoup' would have 3 entries in self.valid_imports
        # 'bs4', 'BeautifulSoup', 'bs4.BeautifulSoup'
        for import_ in dead_import_copy:
            if "." in import_:
                if import_.split(".")[0] in self.valid_imports:
                    print(import_)
                    self.dead_imports.remove(import_)
                    self.valid_imports.append(import_)
                    self.valid_imports.append(import_.split(".")[0])
                    if len(import_.split(".")) > 2:
                        self.dead_imports.append(import_.split(".")[1])
                    continue
                if import_.split(".")[1] in self.valid_imports:
                    print(import_)
                    self.dead_imports.remove(import_)
                    self.valid_imports.append(import_)
                    self.valid_imports.append(import_.split(".")[1])
                    if len(import_.split(".")) > 2:
                        self.dead_imports.append(import_.split(".")[0])
                    continue
            else:
                if import_ in self.valid_imports:
                    print(import_)
                    self.dead_imports.remove(import_)
                    self.valid_imports.append(import_)
        self.dead_imports = list(set(self.dead_imports))
        assert "PyDictionary" not in self.dead_imports


    def remove_unused_imports(self, final_dead_imports):
        """
        Removes unused imports from the file
        :param final_dead_imports: a list of imports that are unused in the entire project
        :return:
        """
        assert "PyDictionary" not in final_dead_imports
        custom_print(f"Removing unused imports from {self.file_location}")
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
                    if line not in final_dead_imports or line not in new_lines:
                        f.write(f"{line}\n")
        except Exception as e:
            custom_print(f"Failed to remove unused imports from {self.file_location}: {e}")
            with open(self.file_location, "w") as f:
                for line in backup_lines:
                    f.write(f"{line}\n")

        if file_changes:
            custom_print(f"Removed unused imports from {self.file_location}")


if __name__ == "__main__":
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
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
        help="Show the version number and exit",
    )
    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Silence all output",
    )
    arguments = parser.parse_args()
    main(arguments)
