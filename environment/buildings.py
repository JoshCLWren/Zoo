from environment.base_elements import Dirt
from organisms.dead_things import Corpse


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
        self.full = self.check_full()

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
            print("Animal position is out of bounds")

    def remove_animal(self, animal):
        """
        This method is called when an animal is removed from the zoo.
        """
        # remove the animal from the grid
        self.grid[animal.position[0]][animal.position[1]] = None
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
        self.plants.remove(plant)
        self.full = self.check_full()
    def remove_water(self, water):
        """
        This method is called when water is removed from the zoo.
        """
        # remove the water from the grid
        self.grid[water.position[0]][water.position[1]] = None
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

    def print_grid(self):
        """
        This method is called when the grid is printed.
        """
        # check for any None values in the grid and replace them with dirt
        for i in range(self.height):
            for j in range(self.width):
                if self.grid[i][j] is None:
                    self.grid[i][j] = Dirt()
        # print the emoji representation of the grid to the console, with each row on a new line
        # print the grid to the console in the form of a matrix
        # center the grid in the console
        for row in self.grid:
            print("".join([cell.emoji for cell in row]))
