import contextlib
import itertools
import logging
import random

import environment.buildings
from organisms.dead_things import Corpse
from organisms.organisms import Organism


class Plant(Organism):
    """
    This is the class for plants.
    """

    def __init__(self, home_id):
        """
        This method is called when the plant is created.
        """
        super().__init__(home_id)
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

    def grow(self):
        """
        This method is called when the plant grows.
        """
        # roll a d100 if it is 1 then the plant grows by 1
        if random.randint(1, 100) == 1:
            self.size += 1

    def die(self):
        """
        This method is called when the plant dies.
        """
        try:
            self.is_alive = False
            self.home_id.plants.remove(self)

            self.home_id.home.grid[self.position[0]][self.position[1]] = None
        except (TypeError, ValueError) as e:
            logging.error(e)

    def __str__(self):
        """
        This method is called when the plant is printed.
        """

        return "Plant"

    def turn(self, turn_number):
        """
        On a plants turn it will grow and then check if it can reproduce.
        """
        # check if the plant is dead
        home = environment.buildings.Zoo.load_instance(self.home_id)
        action = None
        if self.max_age <= self.age:
            self.die()
            return "died"
        self.grow()
        action = "grew"
        # check if the zoo is full
        home.check_full()
        if not home.full:
            self.reproduce()
            action = "reproduced"
        self.age = turn_number - self.birth_turn
        return action

    def check_nearby_tiles(self):
        """
        This method is called when the plant checks the nearby tiles.
        """
        self.nearby_occupied_tiles = []
        self.unoccupied_tiles = []
        self.nearby_unoccupied_tiles = []
        home = environment.buildings.Zoo.load_instance(self.home_id)
        for x, y in itertools.product(range(-1, 2), range(-1, 2)):
            with contextlib.suppress(IndexError):
                if home.grid[self.position[0] + x][self.position[1] + y] is not None:
                    self.nearby_occupied_tiles.append(
                        self.home_id.home.grid[self.position[0] + x][self.position[1] + y]
                    )
                else:
                    self.unoccupied_tiles.append(
                        (self.position[0] + x, self.position[1] + y)
                    )
                    self.nearby_unoccupied_tiles.append(
                        (self.position[0] + x, self.position[1] + y)
                    )

    def reproduce(self):
        """
        A plant will reproduce if it is near an empty tile or another plant or water.
        """
        home = environment.buildings.Zoo.load_instance(self.home_id)

        home.check_full()
        if home.full:
            return
        self.check_nearby_tiles()
        if any(home.grid[x][y] is None for x, y in self.nearby_unoccupied_tiles):
            baby_plant = self.__class__(home_id=self.home_id)
            baby_plant.position = random.choice(self.unoccupied_tiles)
            home.add_plant(baby_plant)
            self.unoccupied_tiles.remove(baby_plant.position)
            self.nearby_unoccupied_tiles.remove(baby_plant.position)


class Tree(Plant):
    """
    This is the class for trees.
    """

    def __init__(self, home_id):
        """
        This method is called when the tree is created.
        """
        super().__init__(home_id)
        self.emoji = "🌳"

    def __str__(self):
        """
        This method is called when the tree is printed.
        """

        return "Tree"


class Bush(Plant):
    """
    This is the class for bushes.
    """

    def __init__(self, home_id):
        """
        This method is called when the bush is created.
        """
        super().__init__(home_id)
        self.emoji = "🌿"

    def __str__(self):
        """
        This method is called when the bush is printed.
        """

        return "Bush"


class Grass(Plant):
    """
    This is the class for grass.
    """

    def __init__(self, home_id):
        """
        This method is called when the grass is created.
        """
        super().__init__(home_id)
        self.emoji = "🌾"

    def __str__(self):
        """
        This method is called when the grass is printed.
        """

        return "Grass"
