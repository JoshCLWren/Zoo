import numpy as np


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

    def add_animal(self, animal):
        """
        This method is called when an animal is added to the zoo.
        """
        # place the animal in the grid
        try:
            self.grid[animal.position[0]][animal.position[1]] = animal
            self.animals.append(animal)
        except IndexError:
            print("Animal position is out of bounds")

    def remove_animal(self, animal):
        """
        This method is called when an animal is removed from the zoo.
        """
        # remove the animal from the grid
        self.grid[animal.position[0]][animal.position[1]] = None
        self.animals.remove(animal)
        # replace the animal with a DeadAnimal
        dead_animal = DeadAnimal(animal)
        self.add_animal(dead_animal)
        dead_animal.decompose()

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
        self.grid[plant.position[0]][plant.position[1]] = plant.__str__()
        self.plants.append(plant)

    def remove_plant(self, plant):
        """
        This method is called when a plant is removed from the zoo.
        """
        # remove the plant from the grid
        self.grid[plant.position[0]][plant.position[1]] = None
        self.plants.remove(plant)

    def remove_water(self, water):
        """
        This method is called when water is removed from the zoo.
        """
        # remove the water from the grid
        self.grid[water.position[0]][water.position[1]] = None
        self.water_sources.remove(water)

    def add_water(self, water):
        """
        This method is called when water is added to the zoo.
        """
        # place the water in the grid
        self.grid[water.position[0]][water.position[1]] = water.__str__()
        self.water_sources.append(water)

    def print_grid(self):
        """
        This method is called when the grid is printed.
        """
        # check for any None values in the grid and replace them with dirt
        for i in range(self.height):
            for j in range(self.width):
                if self.grid[i][j] is None:
                    self.grid[i][j] = Dirt()
        # print the emoji representation of the grid

        print(
            [
                [f" {str(self.grid[i][j].emoji)} " for j in range(self.width)]
                for i in range(self.height)
            ]
        )


class DeadAnimal:
    """
    This is the class for dead animals.
    """

    def __init__(self, former_animal=None):
        """
        This method is called when the dead animal is created.
        """
        self.former_animal = former_animal.__str__()
        self.nutrients = former_animal.size + former_animal.virility
        self.size = former_animal.size
        self.position = former_animal.position
        self.emoji = "💀"

    def decompose(self):
        """
        This method is called when the dead animal decomposes.
        """

        self.size -= 1
        self.nutrients -= 1

    def turn(self, *args, **kwargs):
        """
        This method is called when the dead animal turns.
        """

        self.decompose()


class Dirt:
    """
    This is the class for dirt.
    """

    def __init__(self):
        """
        This method is called when dirt is created.
        """

        self.nutrients = 0
        self.emoji = "🌱"

    def __str__(self):
        """
        This method is called when dirt is printed.
        """

        return "Dirt"
