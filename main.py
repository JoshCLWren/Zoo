"""
Zoo is a game about what happens when the humans disappear and the animals take over.
The game is an overhead view of a zoo, where the player is given the role of one of the animals.
The goal is to survive as long as possible, and to do so the player must eat, sleep, and reproduce.
The player can also interact with other animals, and the player can also interact with the environment.
The player can be a carnivore, herbivore, or omnivore, and the player can be a predator or prey since
it's random what animal the player is.
"""

import itertools
import random

from environment.base_elements import Dirt
from environment.buildings import Zoo
from environment.liquids import Water
from organisms.animals import Animal, Lion, Zebra, Elephant, Hyena, Giraffe, Rhino
from organisms.organisms import LifeException
from organisms.plants import Tree, Bush, Grass


def create_zoo():
    """
    This function creates the zoo.
    """
    # get the system width and height

    zoo = Zoo(height=36, width=60)

    # fill the zoo with random animals
    empty_grid_tiles = zoo.height * zoo.width
    for row, column in itertools.product(range(zoo.height), range(zoo.width)):
        selection = random.choice(["animal", "plant", "water"])
        if selection == "animal":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                animal = random.choice(
                    [
                        Lion,
                        Zebra,
                        Elephant,
                        Hyena,
                        Giraffe,
                        Rhino,
                    ]
                )
                animal = animal()
                animal.position = [row, column]
                zoo.add_animal(animal)
                zoo.grid[row][column] = animal
        elif selection == "plant":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                plant = random.choice(
                    [
                        Tree,
                        Bush,
                        Grass,
                    ]
                )
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


def main():
    """
    This function is the main function.
    """

    # create the zoo
    zoo = create_zoo()

    zoo.print_grid()
    # print the zoo
    turn = 1
    living_animals = 1
    while living_animals:
        # render the zoo

        # run the simulation
        flat_list = [element for sublist in zoo.grid for element in sublist]
        living_animals = [item for item in flat_list if isinstance(item, Animal)]
        living_animals = len(living_animals)
        if not living_animals:
            break

        dead_things = []
        for row in zoo.grid:
            for thing in row:
                if not thing:
                    continue
                if isinstance(thing, (Water, Dirt)):
                    continue
                try:
                    if thing in dead_things:
                        continue
                    if not thing.is_alive:
                        dead_things.append(thing)
                        continue
                    action = thing.turn(zoo.grid, turn_number=turn, zoo=zoo)
                    if action == "died":
                        dead_things.append(thing)
                except LifeException:
                    dead_things.append(thing)
                    # remove the animal from the grid
                    zoo.grid[thing.position[0]][thing.position[1]] = None
        turn += 1



        # print(f"**********Turn {turn}**********")
        # print(f"Zoo has {len(zoo.animals)} animals")
        #
        # print(f"Zoo has {len(zoo.plants)} plants")
        # # if len(zoo.plants) > 100:
        # #     import pdb; pdb.set_trace()
        # #     pass
        # print(f"Zoo has {len(zoo.water_sources)} water sources")

        zoo.check_full()
        # print(f"Zoo is {'full' if zoo.full else 'not full'}")
        # input("Press enter to continue..")
        # clear the screen
        # redraw the grid
        zoo.print_grid()
        # input("Press enter to continue..")




# run the simulation
main()
