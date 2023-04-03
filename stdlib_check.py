import os
import pkgutil
import sys
import sysconfig
from pathlib import Path


def get_builtin_modules():
    return set(sys.builtin_module_names)


def get_c_implemented_modules():
    c_modules = set()
    for importer, module_name, is_pkg in pkgutil.iter_modules():
        if not is_pkg:
            try:
                module = sys.modules[module_name]
            except KeyError:
                continue
            if getattr(module, "__file__", "").endswith(".so"):
                c_modules.add(module_name)
    return c_modules


def get_stdlib_modules():
    stdlib_path = Path(sysconfig.get_path("stdlib"))
    stdlib_modules = set()

    for module_path in stdlib_path.glob("**/*.py"):
        module_name = module_path.relative_to(stdlib_path).stem
        if not module_name.startswith("_"):
            stdlib_modules.add(module_name)

    return stdlib_modules
