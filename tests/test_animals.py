"""
Tests for the behaviour of animal objects.
"""


import itertools
import unittest.mock

import pytest

import environment.liquids
import organisms.animals
import organisms.plants


class TestAnimals:
    """
    Class for tests around the behaviour of Animal objects.
    """

    @pytest.fixture(autouse=True, scope="class")
    def fake_animal(self):
        """
        Create a test animal.
        """
        yield organisms.animals.Animal()

    @pytest.fixture(autouse=True, scope="class")
    def mock_zoo(self):
        """
        Create a test zoo full of plants and water.
        """
        yield environment.buildings.create_zoo(
            height=2, width=2, options=["plant"], plants=[organisms.plants.Grass]
        )

    @pytest.fixture(autouse=True, scope="class")
    def fake_water(self):
        """
        Create a test water.
        """
        yield environment.liquids.Water()

    def test_animals_have_ids(self, fake_animal):
        """
        Test that animals have ids.
        """
        assert fake_animal.id is not None

    def test_animals_can_drink_water(self, mock_zoo, fake_water, fake_animal):
        """
        Test that animals can drink water.
        """
        fake_animal.thirst = 1
        fake_animal.drink(fake_water, mock_zoo)
        assert fake_animal.thirst == 2

    def test_animals_can_eat_food(self, mock_zoo, fake_animal):
        """
        Test that animals can eat food.
        """
        fake_animal.hunger = 1
        fake_animal.position = [0, 0]
        # remove the plant from the grid at the animal's position
        mock_zoo.grid[0][0] = fake_animal
        fake_animal.favorite_food = organisms.plants.Grass
        mock_zoo.grid[0][1] = None
        mock_zoo.grid[0][1] = organisms.plants.Grass()
        mock_zoo.grid[0][1].position = [0, 1]

        fake_animal.eat(mock_zoo.grid[0][1], mock_zoo)
        assert fake_animal.hunger == 2

    def test_animals_can_move(self, mock_zoo, fake_animal):
        """
        Test that animals can move and when they do, the grid is updated without destroying the plant.
        """
        # animal needs to be a bit bigger than grass to move
        fake_animal.size = 2
        assert mock_zoo.grid[0][0].__class__.__name__ == "Animal"
        assert mock_zoo.grid[0][1].__class__.__name__ == "NoneType"
        assert mock_zoo.grid[1][0].__class__.__name__ == "Grass"
        assert mock_zoo.grid[1][1].__class__.__name__ == "Grass"
        direction = [0, 1]
        fake_animal.move(direction, mock_zoo)
        mock_zoo.refresh_grid(visualise=False)
        assert fake_animal.position == [0, 1]
        assert (
            mock_zoo.grid[0][0].__class__.__name__ == "Dirt"
        )  # animal moved, so the old position is now dirt
        assert mock_zoo.grid[0][1].__class__.__name__ == "Animal"
        assert mock_zoo.grid[1][0].__class__.__name__ == "Grass"
        assert mock_zoo.grid[1][1].__class__.__name__ == "Grass"
        # stepping on grass shouldn't turn it to None
        direction = [1, 0]
        fake_animal.move(direction, mock_zoo)
        mock_zoo.refresh_grid(visualise=False)
        assert fake_animal.position == [1, 1]
        assert mock_zoo.grid[0][0].__class__.__name__ == "Dirt"
        assert (
            mock_zoo.grid[0][1].__class__.__name__ == "Grass"
        )  # animal stepped on grass, so it's still there
        assert mock_zoo.grid[1][0].__class__.__name__ == "Grass"
        assert mock_zoo.grid[1][1].__class__.__name__ == "Animal"
