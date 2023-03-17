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

import models


def create_zoo():
    """
    This function creates the zoo.
    """

    zoo = models.park.Zoo(height=10, width=10)

    # fill the zoo with random animals
    empty_grid_tiles = zoo.height * zoo.width
    for row, column in itertools.product(range(zoo.height), range(zoo.width)):
        selection = random.choice(["animal", "plant", "water"])
        if selection == "animal":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                animal = random.choice(
                    [
                        models.organisms.Lion,
                        models.organisms.Zebra,
                        models.organisms.Elephant,
                        models.organisms.Hyena,
                        models.organisms.Giraffe,
                        models.organisms.Rhino,
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
                        models.organisms.Tree,
                        models.organisms.Bush,
                        models.organisms.Grass,
                    ]
                )
                plant = plant()
                plant.position = [row, column]
                zoo.add_plant(plant)
                zoo.grid[row][column] = plant
        elif selection == "water":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                water = models.organisms.Water()
                water.position = [row, column]
                zoo.add_water(water)
                zoo.grid[row][column] = water
        else:
            dirt = models.organisms.Dirt()
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
        living_animals = [
            item for item in flat_list if isinstance(item, models.organisms.Animal)
        ]
        dead_animals = [
            item for item in flat_list if isinstance(item, models.organisms.DeadAnimal)
        ]
        print(f"Zoo has {len(living_animals)} animals")

        for thing in flat_list:
            try:
                thing.turn(zoo.grid, turn_number=turn, zoo=zoo)
            except models.organisms.LifeException:
                print(f"{thing} died")
                # remove the animal from the grid
                zoo.grid[thing.position[0]][thing.position[1]] = None
            except AttributeError:
                print(f"{thing} is not an animal")
        turn += 1

        print(f"**********Turn {turn}**********")
        print(f"Zoo has {len(zoo.animals)} animals")
        zoo.print_grid()
        print(f"Zoo has {len(zoo.plants)} plants")
        print(f"Zoo has {len(zoo.water_sources)} water sources")
        print(f"Zoo has {len(dead_animals)} dead animals")
        input("Press enter to continue..")


# run the simulation
main()
