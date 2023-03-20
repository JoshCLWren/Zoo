"""
Test fixtures needed by multiple test modules.
"""

import pytest

import environment.buildings
import organisms.plants


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
