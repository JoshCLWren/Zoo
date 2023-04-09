import unittest
import argparse
import dependency_cleanup
import os


class TestImportCleaner(unittest.TestCase):
    def mock_args(self):
        """
        Mock the arguments passed to the script
        :return:
        """

    def setUp(self):
        # You can replace the `file_location` with a real Python file that you want to use for testing
        self.file_location = "tests/test_file.py"

    def test_single_line_import(self):
        with open(self.file_location, "w") as f:
            f.write(
                "from pytorch3d.renderer import look_at_view_transform\n"
                "from pytorch3d.renderer import FoVPerspectiveCameras\n"
                "print('Hello World')\n"
            )
        dead_imports = ["pytorch3d"]
        python_file = dependency_cleanup.PythonFile(self.file_location)
        python_file.introspect()
        python_file.remove_unused_imports(dead_imports)
        with open(self.file_location, "r") as f:
            content = f.read()

        self.assertEqual(content, "print('Hello World')\n")

    def test_multiline_import(self):
        with open(self.file_location, "w") as f:
            f.write(
                "from pytorch3d.renderer import (\n"
                "    look_at_view_transform,\n"
                "    FoVPerspectiveCameras,\n"
                "    PointLights,\n"
                "    RasterizationSettings,\n"
                "    MeshRenderer,\n"
                "    MeshRasterizer,\n"
                "    SoftPhongShader,\n"
                "    TexturesVertex,\n"
                ")\n"
                "print('Hello World')\n"
            )
        dead_imports = ["pytorch3d"]
        python_file = dependency_cleanup.PythonFile(self.file_location)
        python_file.introspect()
        python_file.remove_unused_imports(dead_imports)
        with open(self.file_location, "r") as f:
            content = f.read()

        self.assertEqual(content, "print('Hello World')\n")

    def test_unused_pandas_import(self):
        with open(self.file_location, "w") as f:
            f.write("import pandas as pd\n" "print('Hello World')\n")
        dead_imports = ["pandas"]
        python_file = dependency_cleanup.PythonFile(self.file_location)
        python_file.introspect()
        python_file.remove_unused_imports(dead_imports)
        with open(self.file_location, "r") as f:
            content = f.read()

        self.assertEqual(content, "print('Hello World')\n")

    def test_partially_used_multiline(self):
        with open(self.file_location, "w") as f:
            f.write(
                "from pytorch3d.renderer import (\n"
                "    look_at_view_transform,\n"
                "    FoVPerspectiveCameras,\n"
                "    PointLights,\n"
                "    RasterizationSettings,\n"
                "    MeshRenderer,\n"
                "    MeshRasterizer,\n"
                "    SoftPhongShader,\n"
                "    TexturesVertex,\n"
                ")\n"
                "look_at_view_transform()\n"
                "print('Hello World')\n"
            )
        dead_imports = [
            "FoVPerspectiveCameras",
            "PointLights",
            "RasterizationSettings",
            "MeshRenderer",
            "MeshRasterizer",
            "SoftPhongShader",
            "TexturesVertex",
        ]
        python_file = dependency_cleanup.PythonFile(self.file_location)
        python_file.introspect()
        python_file.remove_unused_imports(dead_imports)
        with open(self.file_location, "r") as f:
            content = f.read()
        self.assertEqual(
            content,
            "from pytorch3d.renderer import look_at_view_transform\nlook_at_view_transform()\nprint('Hello World')\n",
        )

    def test_the_word_in(self):
        with open(self.file_location, "w") as f:
            f.write(
                "from organisms.animals import (Animal, Elephant, Giraffe, Hyena, Lion, Rhino,\n"
                "               Zebra)\n"
                "if 1 in [1, 2, 3]:\n"
                "    print('Hello World')\n"
            )
        dead_imports = ["organisms"]
        python_file = dependency_cleanup.PythonFile(self.file_location)
        python_file.introspect()
        python_file.remove_unused_imports(dead_imports)
        with open(self.file_location, "r") as f:
            content = f.read()

        self.assertEqual(content, "if 1 in [1, 2, 3]:\n    print('Hello World')\n")

    def test_doc_string(self):
        """
        In the event a doc string is present, we should not add import statements at the top of the file
        but rather below the doc string
        :return:
        """
        with open(self.file_location, "w") as f:
            f.write(
                '"""\n'
                "This is a doc string\n"
                '"""\n'
                "from pytorch3d.renderer import (\n"
                "    look_at_view_transform,\n"
                "    FoVPerspectiveCameras,\n"
                "    PointLights,\n"
                "    RasterizationSettings,\n"
                ")\n"
                "FoVPerspectiveCameras()\n"
                "print('Hello World')\n"
            )
        dead_imports = ["look_at_view_transform"]
        python_file = dependency_cleanup.PythonFile(self.file_location)
        python_file.introspect()
        python_file.remove_unused_imports(dead_imports)
        with open(self.file_location, "r") as f:
            content = f.read()

        self.assertEqual(
            content,
            '"""\n'
            "This is a doc string\n"
            '"""\n'
            "from pytorch3d.renderer import FoVPerspectiveCameras\n"
            "FoVPerspectiveCameras()\n"
            "print('Hello World')\n",
        )

    def test_requests(self):
        """
        Test that the requests library is not removed from the imports
        :return:
        """
        test_string = "import requests\n"
        test_get = "requests.get('https://www.google.com')\n"
        test_print = "print('Hello World')\n"
        with open(self.file_location, "w") as f:
            f.write(
                test_string
                + test_get
                + test_print
            )
        dead_imports = []
        python_file = dependency_cleanup.PythonFile(self.file_location)
        python_file.introspect()
        python_file.remove_unused_imports(dead_imports)
        with open(self.file_location, "r") as f:
            content = f.read()

        self.assertEqual(content, test_string + test_get + test_print)

        # two remaining tests are needed. import panddas as pd and pd.DataFrame() exists is not working
        # submodules of project level imports are not being removed i.e; from assets import GamesAssets

    def test_aliases(self):
        """
        Test that when an import has an alias and then is used as the alias, it is not removed
        :return:
        """

        test_string_import_alias = "import pandas as pd\n"
        test_non_used_import = "import numpy as np\n"
        test_string_alias = "pd.DataFrame()\n"
        test_print = "print('Hello World')\n"
        with open(self.file_location, "w") as f:
            f.write(
                test_string_import_alias
                + test_non_used_import
                + test_string_alias
                + test_print
            )
        args = argparse.Namespace()
        args.silent = False

        dependency_cleanup.install_pip(args)
        requirements = dependency_cleanup.Requirements(default=True)
        requirements.check_env_packages(args)
        requirements.uninstall_non_default_packages(args)
        requirements.install(args, scan_project=True)
        project_path = os.path.dirname(self.file_location)
        project = dependency_cleanup.Project(project_path=project_path, file=self.file_location)
        requirements.remove_unused_requirements(args)
        project.get_python_files()
        project.get_imports()
        project.filter_imports(requirements)
        assert project.dead_imports == ['numpy']
        assert project.python_files[0].dead_imports == ["numpy"]
        assert project.final_dead_imports == ['numpy']
        assert project.final_import_blocks == ["pandas"]
        project.remove_dead_imports()
        project.validate_requirements(requirements)
        with open(self.file_location, "r") as f:
            content = f.read()

        self.assertEqual(content, test_string_import_alias + test_string_alias + test_print)

if __name__ == "__main__":
    unittest.main()
