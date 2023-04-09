"""
This script scans each python file in the project and checks for unused imports. It then removes them.
"""

import json
import argparse
import ast
import builtins
import contextlib
import logging
import os
import re
import subprocess
import sys
import time
import xmlrpc.client
from typing import List, Tuple

import stdlib_check

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


def main(args, file=None):
    """
    Main function.
    """

    startup_log = "Starting dependency_cleanup..."
    if args:
        global verbose_output
        verbose_output = verbose_output = not args.silent
    else:
        args = argparse.Namespace()
        args.silent = False
        args.project_path = None
        verbose_output = True
    custom_print(startup_log)
    install_pip(args)
    requirements = Requirements(default=True)
    requirements.check_env_packages(args)
    requirements.uninstall_non_default_packages(args)
    requirements.install(args, scan_project=True)
    project_path = args.project_path or os.getcwd()
    project = Project(project_path=project_path, file=file)
    requirements.remove_unused_requirements(args)
    project.get_python_files()
    project.get_imports()
    project.filter_imports(requirements)
    project.remove_dead_imports()
    valid_requirements = project.validate_requirements(requirements)
    requirements.remove_unused_requirements(args)
    requirements.install(args, scan_project=False, dead_imports=project.final_dead_imports, valid_requirements=valid_requirements)
    requirements.check_env_packages(args, dead_imports=project.final_dead_imports)
    requirements.master_txt_file_gen(valid_requirements=valid_requirements, dead_imports=project.final_dead_imports)

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
        "pytest",
        "argparse",
        "pluggy",
        "iniconfig",
        "attrs"
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

    def uninstall_non_default_packages(self, args):
        """
        Uninstall any packages that are not in the default requirements.
        """

        cmd = "pip freeze"
        if args.silent:
            cmd += " -q"
        installed_packages = subprocess.check_output(cmd, shell=True).decode("utf-8")
        if packages_to_uninstall := [
            package.split("==")[0]
            for package in installed_packages.splitlines()
            if package.split("==")[0] not in self.base_requirements
        ]:
            custom_print("Uninstalling non-default packages...")
            cmd = f"pip uninstall {' '.join(packages_to_uninstall)} -y"
            if args.silent:
                cmd += " -q"
            os.system(cmd)


    def install(self, args, scan_project=False, dead_imports=False, valid_requirements=False):
        """
        Install the base requirements for this project and compile a list of requirements.txt
        :return:
        """
        if not self.requirements_installed:
            self.check_env_packages(args)
        if self.packages_to_install:
            custom_print("Installing base requirements...")
            # create a temporary requirements file
            self.install_missing(args, valid_requirements=valid_requirements, dead_imports=dead_imports)
        self.create_requirements_file(scan_project=scan_project)
        self.install_missing(args, dead_imports=dead_imports, valid_requirements=valid_requirements)


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
            self.master_txt_file_gen()

    def master_txt_file_gen(self, dead_imports=False, valid_requirements=False):
        # create a master requirements file
        if os.path.exists("requirements.txt"):
            os.remove("requirements.txt")
        if not isinstance(self.base_requirements, list):
            self.base_requirements = list(self.base_requirements)
        if not isinstance(self.requirements_installed, list):
            self.requirements_installed = list(self.requirements_installed)
        # combine the base requirements with the requirements installed in the environment and write to file
        # with no duplicates
        requirements_set = []
        requirements_set.extend(self.base_requirements)
        requirements_set.extend(self.requirements_installed)
        requirements_set.extend(self.packages_to_install)
        # alphabetize the requirements regardless of case
        requirements_set = set(requirements_set)
        requirements_set = sorted(requirements_set, key=lambda s: s.lower())
        triple_checked_requirements = []
        for package in requirements_set:
            if dead_imports and package in dead_imports:
                continue
            if valid_requirements and package in valid_requirements:
                triple_checked_requirements.append(package)
            if not valid_requirements:
                triple_checked_requirements.append(package)
        requirements_set = triple_checked_requirements
        with open("requirements.txt", "w") as f:
            for package in requirements_set:
                f.write(f"{package}\r")

    def install_missing(self, args, dead_imports=False, valid_requirements=False):
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
                if dead_imports and package in dead_imports:
                    continue
                if valid_requirements and package in valid_requirements:
                    f.write(f"{package}\r")
                if not valid_requirements:
                    f.write(f"{package}\r")
        cmd = f"{sys.executable} -m pip install -r {self.temp_requirements_file}"

        if args.silent:
            cmd += " -q"
        os.system(cmd)
        os.remove(self.temp_requirements_file)
        custom_print("Base requirements installed successfully.")

    def check_env_packages(self, args, dead_imports=False, project_level_imports=False):
        cmd = [sys.executable, "-m", "pip", "freeze"]
        if args.silent:
            cmd.append("-q")
        env_packages = subprocess.check_output(cmd)
        env_packages = env_packages.decode("utf-8").splitlines()

        packages_to_install = self.packages_to_install or []
        # compare this to the requirements.txt file, remove any environment packages that are not in the
        # requirements.txt
        requiments_files_packages = []
        with open("requirements.txt", "r") as f:
            for line in f:
                if (
                    line.strip() in env_packages
                    and line.strip() not in self.base_requirements
                    and line.strip() not in requiments_files_packages
                ):
                    if "BeautifulSoup" in line.strip():
                        # this is a special case, the package name is different than the import name
                        continue
                    if dead_imports and line.strip() in dead_imports:
                        continue
                    if project_level_imports and line.strip() in project_level_imports:
                        continue
                    self.packages_to_remove.append(line.strip())
                requiments_files_packages.append(line.strip())
        for package in env_packages:
            if package in requiments_files_packages:
                packages_to_install.append(package)
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

    def __init__(self, project_path=None, silent=False, file=None):
        self.PROJECT_PATH = project_path or os.path.dirname(os.path.abspath(__file__))
        custom_print(self.PROJECT_PATH)
        # start by installing the requirements

        custom_print("Installed requirements")
        # List of files to ignore
        self.IGNORE_FILES = ["dependency_cleanup.py", "stdlib_check.py", "test_deps.py"]
        if file:
            python_file_instance = PythonFile(file)
            self.python_files = [python_file_instance]
        else:
            self.python_files = []
        custom_print("Ignoring files: ", self.IGNORE_FILES)
        # add .gitignore to ignore files
        with contextlib.suppress(FileNotFoundError):
            with open(os.path.join(self.PROJECT_PATH, ".gitignore")) as f:
                self.IGNORE_FILES.extend(f.read().splitlines())
        custom_print("Ignoring files: ", self.IGNORE_FILES)
        # List of directories to ignore
        self.IGNORE_DIRS = [".git", "venv", "images", ".idea"]
        custom_print("Ignoring directories: ", self.IGNORE_DIRS)
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
        if not self.python_files:
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
        used_imports = []
        for file in self.python_files:
            custom_print(f"Scanning {file} for imports")
            file.introspect()
            custom_print(f"Found {len(file.imports)} imports in {file.file_location}")
            self.import_blocks.extend(file.imports)
            self.dead_imports.extend(file.dead_imports)
            used_imports.extend(file.valid_imports)
        # remove used_imports from dead_imports
        self.dead_imports = list(set(self.dead_imports) - set(used_imports))
        self.import_blocks.extend(used_imports)
        assert "requests" in self.import_blocks
        # remove duplicates
        self.import_blocks = list(set(self.import_blocks))
        custom_print(f"Found {len(self.import_blocks)} used imports in all files")
        self.dead_imports = list(set(self.dead_imports))
        custom_print(f"Found {len(self.dead_imports)} unused imports in all files")

    def filter_imports(self, requirements_instance):
        """
        Filter out any imports that don't need to be installed or removed.
        :param requirements_instance:
        :return:
        """
        # find any imports that are not external packages requiring installation by pip
        assert "requests" in self.import_blocks
        self.skipped_libraries = stdlib_check.Builtins().get()
        self.import_blocks = self.filter_unique_tokens(self.import_blocks)
        # filter out any imports that may be importing a project file or module
        self.projects_modules = self.inspect_project_level_imports()
        # add the project level imports to the skipped libraries list so they are not attempted to be installed
        self.skipped_libraries.extend(self.projects_modules)
        self.skipped_libraries = self.dedupe_list(self.skipped_libraries)
        # inspect the dead imports to see if they are project level imports
        self.dead_imports = self.filter_unique_tokens(self.dead_imports)
        # inspect the import blocks to see if they are project level imports as well
        self.import_blocks = self.filter_unique_tokens(self.import_blocks)

        # ensure that final import blocks does not contain any dead imports, this prevents the script from trying to
        # install packages that are either standard libraries or project level imports
        # final_import_blocks is used to install packages
        self.final_import_blocks = [
            import_block
            for import_block in self.import_blocks
            if import_block not in self.dead_imports
        ]
        # ensure that final dead imports does not contain any import blocks that are skipped
        # this prevents the script from trying to remove standard libraries or project level imports
        # from python file import statements
        # final_dead_imports is used to remove imports from python files
        self.final_dead_imports = [
            import_block
            for import_block in self.dead_imports
            if import_block not in self.skipped_libraries
        ]
        self.final_dead_imports = self.dedupe_list(self.final_dead_imports)
        assert "requests" in self.final_import_blocks
        requirements_instance.packages_to_install.extend(self.final_import_blocks)

    def inspect_project_level_imports(self):
        """
        Create a list of what could be project level imports
        :return:
        """
        project_files = []
        project_folders = []
        for file in self.python_files:
            # remove the project path from the file location
            file_location = file.file_location.replace(self.PROJECT_PATH, "")
            # split to see if it is a top level file or a module
            split_file_location = file_location.split(os.sep)
            if len(split_file_location) == 1:
                # top level file
                project_files.append(split_file_location[0].replace(".py", ""))
            else:
                # module
                # remove the file name from the file location
                project_files.append(split_file_location[-1].replace(".py", ""))
                # add all remaining folders to the project folders list
                project_folders.extend(split_file_location[:-1])
        project_files = self.dedupe_list(project_files)
        project_folders = self.dedupe_list(project_folders)
        self.projects_modules.extend(project_files)
        self.projects_modules.extend(project_folders)
        self.projects_modules = self.dedupe_list(self.projects_modules)
        return self.projects_modules

    @staticmethod
    def dedupe_list(list_to_dedupe):
        """
        Convert a list to a set to remove duplicates and then convert back to a list
        :param list_to_dedupe:
        :return: list of unique items
        """
        return list(set(list_to_dedupe))

    def filter_unique_tokens(self, import_blocks):
        """
        Split any import blocks that are importing a module or submodule
        Check if the import blocks are in self.skipped_libraries and if so remove them
        :param import_blocks: list of import blocks
        :return: list of import blocks without any skipped libraries
        """
        live_modules, live_sub_modules = [], []
        for block in import_blocks:
            if block == "requests":
                pass
            if "." in block:
                split_mod = block.split(".")
                if split_mod[0] in self.skipped_libraries:
                    # prevent submodules from being added to the list of imports to be installed
                    # if the parent module is a skipped library
                    continue
                live_modules.append(split_mod[0])
                live_sub_modules.append(split_mod[1])
        import_blocks.extend(live_modules)
        import_blocks.extend(live_sub_modules)
        unique_blocks = self.dedupe_list(import_blocks)
        blocks = [block for block in unique_blocks if block not in self.skipped_libraries]
        return blocks

    def remove_dead_imports(self):
        """
        Remove any unused imports from python files by calling the remove_unused_imports method on each file
        :return:
        """
        assert "requests" not in self.final_dead_imports
        for file in self.python_files:
            file.remove_unused_imports(self.final_dead_imports)

    def validate_requirements(self, requirements_instance):

        # check if the validated requirement cache exists
        invalid_requirements = []
        validated_cache_file = "validated_requirements.json"
        invalid_requirements_file = "invalid_requirements.json"
        if os.path.exists(validated_cache_file):
            with open(validated_cache_file, "r") as file:
                try:
                    validated_requirements = json.load(file)
                except json.decoder.JSONDecodeError:
                    validated_requirements = []
        else:
            validated_requirements = []
        if "BeautifulSoup" in validated_requirements: # Some packages are named differently on PyPI than they are on GitHub
            new_requirements = [requirement for requirement in validated_requirements if requirement != "BeautifulSoup"]
            validated_requirements = new_requirements
            invalid_requirements.append("BeautifulSoup")
        # check if the invalid requirements cache exists
        if os.path.exists(invalid_requirements_file):
            with open(invalid_requirements_file, "r") as file:
                with contextlib.suppress(json.decoder.JSONDecodeError):
                    invalid_requirements = json.load(file)
        self.final_import_blocks = list(set(self.final_import_blocks))
        for import_block in self.final_import_blocks:
            # check if the import block is cached in either the validated or invalid requirements cache
            if import_block in validated_requirements:
                continue
            if import_block in invalid_requirements:
                continue
            if import_block in self.skipped_libraries:
                print(f"Skipping {import_block} as it matches a skipped library")
                continue
            if "." in import_block:
                try:
                    import_block_prefix = import_block.split(".")[0]
                    import_block_suffix = import_block.split(".")[1]
                    if import_block_prefix in self.skipped_libraries:
                        print(f"Skipping {import_block} as it's prefix matches a skipped library")
                        invalid_requirements.append(import_block)
                        continue

                    if import_block_suffix in self.skipped_libraries:
                        print(f"Skipping {import_block} as it's suffix matches a skipped library")
                        invalid_requirements.append(import_block)
                        continue
                    for block in self.skipped_libraries:
                        possible_skip_reason = ""
                        if import_block_prefix in block:
                            possible_skip_reason += f" import block prefix {import_block_prefix} is a partial match for {block}"
                        if import_block_suffix in block:
                            possible_skip_reason += f" import block suffix {import_block_suffix} is a partial match for {block}"
                        if possible_skip_reason != "":
                            user_decision = input(
                                f"We have detected that {import_block} is a partial match for {block}. Due to: {possible_skip_reason}. Do you want to skip this import block? (y/n)"
                            )
                            if user_decision.lower() == "y":
                                print(f"Skipping {import_block} as it matches a skipped library")
                                invalid_requirements.append(import_block)
                                continue
                    import_block = import_block_prefix
                except Exception as e:
                    custom_print(f"Failed to remove . from {import_block}: {e}")
                    invalid_requirements.append(import_block)
                    continue
            if (
                import_block not in self.skipped_libraries
                or import_block not in invalid_requirements
            ) and import_block not in validated_requirements:
                if package := self.package_exists_on_pypi(import_block):
                    requirements_instance.packages_to_install.append(package)
                    validated_requirements.append(package)
                else:
                    invalid_requirements.append(import_block)
        # cache the invalid requirements so we can use them later
        with open(invalid_requirements_file, "w") as f:
            invalid_requirements = list(set(invalid_requirements))
            if "BeautifulSoup" not in invalid_requirements:
                invalid_requirements.append("BeautifulSoup")
            json.dump(invalid_requirements, f)
        with open(validated_cache_file, "w") as f:
            validated_requirements = list(set(validated_requirements))
            if "BeautifulSoup" in validated_requirements:
                new_requirements = [requirement for requirement in validated_requirements if requirement != "BeautifulSoup"]
                validated_requirements = new_requirements
            json.dump(validated_requirements, f)
        return list(set(validated_requirements))

    def package_exists_on_pypi(self, package_name, retry_count=0):
        pypi_package_aliases = (
            {  # there are some packages that have changed names on pypi
                "PIL": "Pillow",  # Pillow is the new name for PIL
                "bs4": "beautifulsoup4",  # beautifulsoup4 is the new name for bs4
            }
        )
        # if somehow we've gotten into a state where we're trying to install a package that is skipped, return False

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
        with open(self.file_location, "r") as file:
            tree = ast.parse(file.read())

        imported_names = set()
        imported_full_names = {}
        aliases = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    imported_name = None
                    import_alias = None
                    if isinstance(node, ast.Import):
                        imported_name = alias.name
                        # chaeck if the alias has an asname and add it to the import_names set
                        with contextlib.suppress(Exception):
                            import_alias = alias.asname
                            aliases.append({"name": alias.name, "asname": alias.asname})
                    elif isinstance(node, ast.ImportFrom):
                        imported_name = (
                            alias.name
                            if node.module is None
                            else f"{node.module}.{alias.name}"
                        )
                    if imported_name is not None:
                        self.imports.append(imported_name)
                        imported_names.add(alias.name)
                        if import_alias is not None:
                            imported_names.add(import_alias)
                        imported_full_names[alias.name] = imported_name

        class UsageVisitor(ast.NodeVisitor):
            def __init__(self, imported_names):
                self.imported_names = imported_names
                self.used_names = set()

            def visit_Name(self, node):
                if node.id in self.imported_names:
                    self.used_names.add(node.id)

        visitor = UsageVisitor(imported_names)
        visitor.visit(tree)

        for name in visitor.used_names:
            if name in [package["asname"] for package in aliases]:
                # find the name in aliases that the asname corresponds to
                for alias in aliases:
                    if alias["asname"] == name:
                        self.valid_imports.append(alias["name"])
            try:
                self.valid_imports.append(imported_full_names[name])
            except KeyError:
                self.valid_imports.append(name)

        for import_ in self.imports:
            if import_ not in self.valid_imports:
                self.dead_imports.append(import_)
        dead_imports = self.dead_imports.copy()
        final_dead_imports = []

        for dead_import in dead_imports:
            for alias in aliases:
                if dead_import == alias["name"]:
                    # check if the alias["asname"] is in the valid imports
                    if alias["asname"] not in self.valid_imports:
                        final_dead_imports.append(dead_import)
                if dead_import == alias["asname"]:
                    # ensure that the alias["name"] is not in the valid imports
                    if alias["name"] not in self.valid_imports:
                        final_dead_imports.append(dead_import)
        self.dead_imports = final_dead_imports

        self.valid_imports = list(set(self.valid_imports))
        self.dead_imports = list(set(self.dead_imports))

    def remove_unused_imports(self, final_dead_imports):
        """
        Removes unused imports from the file
        :param final_dead_imports: a list of imports that are unused in the entire project
        :return:
        """
        assert "PyDictionary" not in final_dead_imports
        custom_print(f"Removing unused imports from {self.file_location}")

        with open(self.file_location) as f:
            lines = f.readlines()

        backup_lines = lines.copy()

        def is_line_unused_import(code_line):
            tokens = [code_line]
            # split by any non alphanumeric character
            for token in re.split(r"\W+", code_line):
                if token not in ["", "import", "from", "as"]:
                    tokens.append(token)
            if any(token in final_dead_imports for token in tokens):
                return True

        new_lines = []
        multiline_import = False
        multiline_imports = []
        modified_multiline_imports = {}
        multi_line_string = ""
        for index, line in enumerate(lines):
            if "import (" in line:
                multiline_import = True
                multi_line_string = line
                if is_line_unused_import(line):
                    continue
            if ")" in line and multiline_import:
                multiline_import = False
                multi_line_string = multi_line_string + line
                multiline_imports.append(
                    {"full_string": multi_line_string, "usages": []}
                )
                continue
            if multiline_import:
                multi_line_string = multi_line_string + line
                continue
            if not multiline_import and is_line_unused_import(line):
                continue

            if line in ["", "import", "from", "as"]:
                continue
            new_lines.append(line)

            line_tokens = re.split(r"\W+", line)
            for line_token in line_tokens:
                if line_token == "":
                    continue
                for long_import in multiline_imports:
                    if line_token in long_import["full_string"]:
                        if modified_multiline_imports.get(long_import["full_string"]):
                            modified_multiline_imports[
                                long_import["full_string"]
                            ].append(line_token)
                        modified_multiline_imports[long_import["full_string"]] = [
                            line_token
                        ]
        if modified_multiline_imports:
            for found_uses in modified_multiline_imports:
                new_lines_copy = new_lines.copy()
                import_prefix = "from " if "from" in found_uses else "import "
                package = found_uses.split(" ")[1]
                import_prefix = (
                    import_prefix + package + " import "
                    if "from" in found_uses
                    else import_prefix + package + " ("
                )
                new_import_statement = import_prefix + ", ".join(
                    modified_multiline_imports[found_uses]
                )
                # add the new import statement to the new lines but in the beginning
                if "(" in new_import_statement:
                    new_import_statement = f"{new_import_statement})\n"
                else:
                    new_import_statement = f"{new_import_statement}\n"
                # check the last word of the import statement if its "in" or "as" then remove it then do not add a new line
                index_to_insert = 0
                # if the file has a docstring then insert the new import statement after the docstring
                if new_lines_copy[0].startswith('"""'):
                    # find the end of the docstring
                    triple_quote_count = 0
                    for index, line in enumerate(new_lines_copy):
                        if '"""' in line:
                            triple_quote_count += 1
                        if triple_quote_count == 2:
                            index_to_insert = index + 1  # insert after the docstring
                            break

                if new_import_statement.split(" ")[-1] not in ["in\n", "as\n"]:
                    new_lines_copy.insert(index_to_insert, new_import_statement)
                    new_lines = new_lines_copy
        file_changes = "".join(lines) != "".join(new_lines)
        try:
            with open(self.file_location, "w") as f:
                for line in new_lines:
                    # check the last word of the import statement if its "in" or "as" then remove it then do not add a new line
                    if line.split(" ")[-1] not in ["in", "as"]:
                        f.write(line)

        except Exception as e:
            custom_print(
                f"Failed to remove unused imports from {self.file_location}: {e}"
            )
            with open(self.file_location, "w") as f:
                for line in backup_lines:
                    f.write(line)

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
