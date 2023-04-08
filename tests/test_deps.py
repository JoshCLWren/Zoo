import unittest

import dependency_cleanup


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


if __name__ == "__main__":
    unittest.main()
