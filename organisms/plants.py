import contextlib
import itertools
import random

from organisms.dead_things import Corpse
from organisms.organisms import Organism


class Plant(Organism):
    """
    This is the class for plants.
    """

    def __init__(self):
        """
        This method is called when the plant is created.
        """
        self.size = 1
        self.age = 1
        self.nutrition = 1
        self.favorite_food = Corpse
        self.position = [0, 0]
        self.emoji = "🌱"
        self.max_age = 15 * 365
        self.nearby_occupied_tiles = []
        self.unoccupied_tiles = []
        self.nearby_unoccupied_tiles = []
        self.birth_turn = 1
        super().__init__()

    def grow(self):
        """
        This method is called when the plant grows.
        """

        self.size += 1

    def die(self, zoo):
        """
        This method is called when the plant dies.
        """
        try:
            self.is_alive = False
            zoo.plants.remove(self)

            zoo.grid[self.position[0]][self.position[1]] = None
        except (TypeError, ValueError) as e:
            print(e)

    def __str__(self):
        """
        This method is called when the plant is printed.
        """

        return "Plant"

    def turn(self, grid, turn_number, zoo):
        """
        On a plants turn it will grow and then check if it can reproduce.
        """
        # check if the plant is dead
        action = None
        if self.max_age <= self.age:
            self.die(zoo)
            return "died"
        self.grow()
        action = "grew"
        # check if the zoo is full
        zoo.check_full()
        if not zoo.full:
            self.reproduce(grid, zoo)
            action = "reproduced"
        self.age = turn_number - self.birth_turn
        return action

    def check_nearby_tiles(self, grid):
        """
        This method is called when the plant checks the nearby tiles.
        """
        self.nearby_occupied_tiles = []
        self.unoccupied_tiles = []
        self.nearby_unoccupied_tiles = []
        for x, y in itertools.product(range(-1, 2), range(-1, 2)):
            with contextlib.suppress(IndexError):
                if grid[self.position[0] + x][self.position[1] + y] is not None:
                    self.nearby_occupied_tiles.append(
                        grid[self.position[0] + x][self.position[1] + y]
                    )
                else:
                    self.unoccupied_tiles.append(
                        (self.position[0] + x, self.position[1] + y)
                    )
                    self.nearby_unoccupied_tiles.append(
                        (self.position[0] + x, self.position[1] + y)
                    )

    def reproduce(self, grid, zoo):
        """
        A plant will reproduce if it is near an empty tile or another plant or water.
        """
        zoo.check_full()
        if zoo.full:
            return
        self.check_nearby_tiles(grid)
        if any(grid[x][y] is None for x, y in self.nearby_unoccupied_tiles):
            baby_plant = self.__class__()
            baby_plant.position = random.choice(self.unoccupied_tiles)
            zoo.add_plant(baby_plant)
            self.unoccupied_tiles.remove(baby_plant.position)
            self.nearby_unoccupied_tiles.remove(baby_plant.position)


class Tree(Plant):
    """
    This is the class for trees.
    """

    def __init__(self):
        """
        This method is called when the tree is created.
        """
        self.emoji = "🌳"
        super().__init__()

    def __str__(self):
        """
        This method is called when the tree is printed.
        """

        return "Tree"


class Bush(Plant):
    """
    This is the class for bushes.
    """

    def __init__(self):
        """
        This method is called when the bush is created.
        """
        self.emoji = "🌿"
        super().__init__()

    def __str__(self):
        """
        This method is called when the bush is printed.
        """

        return "Bush"


class Grass(Plant):
    """
    This is the class for grass.
    """

    def __init__(self):
        """
        This method is called when the grass is created.
        """
        self.emoji = "🌾"
        super().__init__()

    def __str__(self):
        """
        This method is called when the grass is printed.
        """

        return "Grass"
