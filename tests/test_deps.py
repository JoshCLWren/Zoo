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
        dead_imports = [
            "pytorch3d"
        ]
        python_file = dependency_cleanup.PythonFile(self.file_location)
        python_file.introspect()
        python_file.remove_unused_imports(dead_imports)
        with open(self.file_location, "r") as f:
            content = f.read()

        self.assertEqual(content, "print('Hello World')\n")

    def test_unused_pandas_import(self):
        with open(self.file_location, "w") as f:
            f.write(
                "import pandas as pd\n"
                "print('Hello World')\n"
            )
        dead_imports = [
            "pandas"
        ]
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
        self.assertEqual(content, "from pytorch3d.renderer import look_at_view_transform\nlook_at_view_transform()\nprint('Hello World')\n")

    def test_the_word_in(self):
        with open(self.file_location, "w") as f:
            f.write(
                "from organisms.animals import invertebrates\n"
                "if 1 in [1, 2, 3]:\n"
                "    print('Hello World')\n"
            )
        dead_imports = [
            "organisms"
        ]
        python_file = dependency_cleanup.PythonFile(self.file_location)
        python_file.introspect()
        python_file.remove_unused_imports(dead_imports)
        with open(self.file_location, "r") as f:
            content = f.read()

        self.assertEqual(content, "if 1 in [1, 2, 3]:\n    print('Hello World')\n")
if __name__ == "__main__":
    unittest.main()
