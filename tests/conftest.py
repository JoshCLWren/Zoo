"""
Test fixtures needed by multiple test modules.
"""
try:
    # somtimes pytest is not installed due to the dependency checker not working properly
    import pytest
    import os
except ImportError:
    import os
    os.system("pip install pytest")

# due to the nature of the dependency checker, we need to import the modules and install the dependencies
for import_statement in ("import environment.buildings", "import organisms.plants"):
    while True:
        try:
            exec(import_statement)
            break
        except ModuleNotFoundError as e:
            print(f"ModuleNotFoundError: {e}")
            module_needed = e.name
            os.system(f"pip install {module_needed}")
        except ImportError as e:
            print(f"ImportError: {e}")
            break

@pytest.fixture(autouse=True)
def install_requirements():
    """
    Install requirements before running tests.
    """
    # create a file with the current environment's dependencies
    os.system("pip freeze > current_deps.txt")
    current_deps = []
    needed_deps = []
    with open("current_deps.txt") as current:
        current_deps.extend(current.readlines())
    with open("test_deps.txt") as needed:
        needed_deps.extend(needed.readlines())
    need_installing = [dep for dep in needed_deps if dep not in current_deps]
    if need_installing:
        os.system("pip install -r test_deps.txt")

@pytest.fixture()
def mock_zoo():
    """
    Create a test zoo full of plants and water.
    """
    yield environment.buildings.create_zoo(
        height=2, width=2, options=["plant"], plants=[organisms.plants.Grass]
    )


@pytest.fixture()
def fake_animal(mock_zoo):
    """
    Create a test animal.
    """
    yield organisms.animals.Animal(home_id=mock_zoo.id)


@pytest.fixture()
def fake_water(mock_zoo):
    """
    Create a test water.
    """
    x_pos, y_pos = 0, 0
    water = environment.liquids.Water(home_id=mock_zoo.id)
    mock_zoo.grid[x_pos][y_pos] = water
    mock_zoo.reprocess_tiles()
    yield water
