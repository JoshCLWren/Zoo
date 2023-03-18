import contextlib
import itertools
import random

from environment.base_elements import Dirt
from environment.liquids import Water
from organisms.animals import Elephant, Giraffe, Hyena, Lion, Rhino, Zebra, Animal
from organisms.dead_things import Corpse
from organisms.plants import Bush, Grass, Tree
import logging



class Zoo:
    """
    This is the class for the zoo.
    """

    def __init__(self, height, width):
        """
        This method is called when the zoo is created.
        """
        self.animals = []
        self.plants = []
        self.water_sources = []
        self.height = height
        self.width = width
        # grid is a matrix of the same size as the zoo
        # it contains the string representation of the animal at that position
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.full = False
        self.tiles_to_refresh = []

    def check_full(self):
        """
        This method checks if the zoo is full.
        """
        # check if there are any empty positions in the grid
        max_capacity = self.height * self.width
        if len(self.plants) > max_capacity:
            return True
        for row in self.grid:
            for cell in row:
                if cell:
                    max_capacity -= 1
        self.full = max_capacity == 0

    def add_animal(self, animal):
        """
        This method is called when an animal is added to the zoo.
        """
        # place the animal in the grid
        try:
            if not self.full:
                self.grid[animal.position[0]][animal.position[1]] = animal
                self.animals.append(animal)

        except IndexError:
            logging.error("Animal position is out of bounds")

    def remove_animal(self, animal):
        """
        This method is called when an animal is removed from the zoo.
        """
        # remove the animal from the grid
        self.grid[animal.position[0]][animal.position[1]] = None
        with contextlib.suppress(ValueError):
            self.animals.remove(animal)
        # replace the animal with a DeadAnimal
        dead_animal = Corpse(animal)
        self.add_animal(dead_animal)
        dead_animal.decompose()
        self.full = self.check_full()

    def __str__(self):
        """
        This method is called when the zoo is printed.
        """

        return "Zoo"

    def add_plant(self, plant):
        """
        This method is called when a plant is added to the zoo.
        """
        # place the plant in the grid
        if not self.full:
            self.grid[plant.position[0]][plant.position[1]] = plant
            self.plants.append(plant)

    def remove_plant(self, plant):
        """
        This method is called when a plant is removed from the zoo.
        """
        # remove the plant from the grid
        dirty_where_plant_was = Dirt(plant.position)
        self.grid[plant.position[0]][plant.position[1]] = dirty_where_plant_was
        with contextlib.suppress(ValueError):
            self.plants.remove(plant)
        self.full = self.check_full()

    def remove_water(self, water):
        """
        This method is called when water is removed from the zoo.
        """
        # remove the water from the grid
        self.grid[water.position[0]][water.position[1]] = None
        with contextlib.suppress(ValueError):
            self.water_sources.remove(water)
        self.full = self.check_full()

    def add_water(self, water):
        """
        This method is called when water is added to the zoo.
        """
        # place the water in the grid
        if not self.full:
            self.grid[water.position[0]][water.position[1]] = water.__str__()
            self.water_sources.append(water)

    def refresh_grid(self, visualise=True):
        """
        This method is called when the grid is printed.
        """

        # check self.tiles_to_refresh and replace the tiles with what they were before an animal moved
        # to that tile
        tiles_to_refresh = []
        #remove and None values from self.tiles_to_refresh
        self.tiles_to_refresh = [tile for tile in self.tiles_to_refresh if tile is not None]
        for tile in self.tiles_to_refresh:
            # check if the tile is occupied by an animal
            if not issubclass(
                self.grid[tile.position[0]][tile.position[1]].__class__, Animal
            ):
                # if it is, replace the tile with the animal
                self.grid[tile.position[0]][tile.position[1]] = tile
            else:
                # if it isn't, add it to the list of tiles to refresh
                tiles_to_refresh.append(tile)

        self.tiles_to_refresh = tiles_to_refresh

        # fill any vacant tiles with dirt
        for i in range(self.height):
            for j in range(self.width):
                if self.grid[i][j] is None:
                    # check if the tile is next to water and if so make it grass
                    north_neighbour = self.grid[i - 1][j] if i > 0 else None
                    south_neighbour = (
                        self.grid[i + 1][j] if i < self.height - 1 else None
                    )
                    east_neighbour = self.grid[i][j + 1] if j < self.width - 1 else None
                    west_neighbour = self.grid[i][j - 1] if j > 0 else None
                    north_east_neighbour = (
                        self.grid[i - 1][j + 1]
                        if i > 0 and j < self.width - 1
                        else None
                    )
                    north_west_neighbour = (
                        self.grid[i - 1][j - 1] if i > 0 and j > 0 else None
                    )
                    south_east_neighbour = (
                        self.grid[i + 1][j + 1]
                        if i < self.height - 1 and j < self.width - 1
                        else None
                    )
                    south_west_neighbour = (
                        self.grid[i + 1][j - 1]
                        if i < self.height - 1 and j > 0
                        else None
                    )
                    neighbors = {
                        "north": north_neighbour,
                        "south": south_neighbour,
                        "east": east_neighbour,
                        "west": west_neighbour,
                        "north_east": north_east_neighbour,
                        "north_west": north_west_neighbour,
                        "south_east": south_east_neighbour,
                        "south_west": south_west_neighbour,
                    }
                    for neighbor in neighbors.values():
                        if neighbor and neighbor.__class__ == Water or neighbor.__class__ == Grass:
                            self.grid[i][j] = Grass()
                            self.grid[i][j].position = (i, j)
                            break
                    else:
                        self.grid[i][j] = Dirt()
                        self.grid[i][j].position = (i, j)

        # print the emoji representation of the grid to the console, with each row on a new line
        # print the grid to the console in the form of a matrix
        # center the grid in the console
        if visualise:
            for row in self.grid:
                print("".join([cell.emoji for cell in row]))


def create_zoo(height=35, width=65, options=None, animals=None, plants=None):
    """
    This function creates the zoo.
    """
    # get the system width and height

    if options is None:
        options = ["animal", "plant", "water"]
    zoo = Zoo(height=height, width=width)

    # fill the zoo with random animals
    empty_grid_tiles = zoo.height * zoo.width
    for row, column in itertools.product(range(zoo.height), range(zoo.width)):
        selection = random.choice(options)
        if selection == "animal":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                animal = random.choice(animals)
                animal = animal()
                animal.position = [row, column]
                zoo.add_animal(animal)
                zoo.grid[row][column] = animal
        elif selection == "plant":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                plant = random.choice(plants)
                plant = plant()
                plant.position = [row, column]
                zoo.add_plant(plant)
                zoo.grid[row][column] = plant
        elif selection == "water":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                water = Water()
                water.position = [row, column]
                zoo.add_water(water)
                zoo.grid[row][column] = water
        else:
            dirt = Dirt()
            dirt.position = [row, column]
            zoo.grid[row][column] = dirt
    return zoo
