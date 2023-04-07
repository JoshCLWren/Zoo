import json
import os
import pkgutil
import sys
import sysconfig
from pathlib import Path


def remove_leading_underscore(module):
    return [m[1:] if m.startswith("_") else m for m in module]


class Builtins:
    """
    A class for checking if a module is a builtin module.
    """

    def __init__(self):
        self.use_cache = True
        self.modules = set()
        self.cache_path = "cache/builtins.json"
        self.cache_dict = {
            "builtin_modules": [],
            "c_implemented_modules": [],
            "stdlib_modules": [],
            "python_system_files": [],
            "modules": [],
        }

    def builtin_modules(self):
        name = "builtin_modules"
        if self.use_cache:
            output = self.check_if_cached(name)
            if output:
                return output
        output = remove_leading_underscore(set(sys.builtin_module_names))
        return self.cache_output(output, name)

    def cache_output(self, obj, name):
        self.cache_dict[name] = set(list(obj))
        self.save_cache()
        return self.cache_dict[name]

    def save_cache(self):
        # make sure the cache directory exists and create it if it doesn't
        # cast the set to a list so it can be serialized
        for key, value in self.cache_dict.items():
            self.cache_dict[key] = list(value)
        if not os.path.exists("cache"):
            os.mkdir("cache")
        with open(self.cache_path, "w") as f:
            json.dump(self.cache_dict, f)

    def c_implemented_modules(self):
        name = "c_implemented_modules"
        if self.use_cache:
            output = self.check_if_cached(name)
            if output:
                return output
        c_modules = set()
        for importer, module_name, is_pkg in pkgutil.iter_modules():
            if not is_pkg:
                try:
                    module = sys.modules[module_name]
                except KeyError:
                    continue
                if getattr(module, "__file__", "").endswith(".so"):
                    c_modules.add(module_name)

        output = remove_leading_underscore(c_modules)
        return self.cache_output(output, name)

    def stdlib_modules(self):
        name = "stdlib_modules"
        if self.use_cache:
            output = self.check_if_cached(name)
            if output:
                return output
        stdlib_path = Path(sysconfig.get_path("stdlib"))
        stdlib_modules = set()

        for module_path in stdlib_path.glob("**/*.py"):
            module_name = module_path.relative_to(stdlib_path).stem
            stdlib_modules.add(module_name)
        output = remove_leading_underscore(stdlib_modules)
        return self.cache_output(output, name)

    def python_system_files(self):
        name = "python_system_files"
        if self.use_cache:
            output = self.check_if_cached(name)
            if output:
                return output
        python_system_files = []
        # find the python path
        python_path = Path(sysconfig.get_path("stdlib"))
        # find all the files and folders in the python path
        for file in python_path.glob("**/*"):
            # if the file is a python file
            if file not in python_system_files:
                if file.suffix == ".py":
                    # add the file to the set
                    python_system_files.append(file.name[:-3])
                # also add the folder to the set
                if file.is_dir():
                    python_system_files.append(file.name)

        output = remove_leading_underscore(set(python_system_files))
        return self.cache_output(output, name)

    def combine(self):
        name = "modules"
        if self.use_cache:
            output = self.check_if_cached(name)
            if output:
                self.modules = output
                return output
        output = (
            self.builtin_modules()
            + self.c_implemented_modules()
            + self.stdlib_modules()
            + self.python_system_files()
        )
        self.modules = self.cache_output(output, name)
        return self.modules

    def check_if_cached(self, obj):
        """
        Check if the module is cached.
        :param obj: The key to check for in the cache json or the dict.
        :return: dict or None
        """
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r") as f:
                self.cache_dict = json.load(f)
            if obj in self.cache_dict and len(self.cache_dict[obj]) > 0:
                return self.cache_dict[obj]
        return None

    def get(self, filtered_by=None):
        self.stdlib_modules()
        self.python_system_files()
        self.c_implemented_modules()
        self.builtin_modules()
        self.combine()
        if filtered_by:
            self.filter_by(filtered_by)
        return self.modules

    def filter_by(self, obj):
        self.modules = set([module for module in self.modules if module in obj])

        return self.modules
