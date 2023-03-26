"""
Zoo is a game about what happens when the humans disappear and the animals take over.
The game is an overhead view of a zoo, where the player is given the role of one of the animals.
The goal is to survive as long as possible, and to do so the player must eat, sleep, and reproduce.
The player can also interact with other animals, and the player can also interact with the environment.
The player can be a carnivore, herbivore, or omnivore, and the player can be a predator or prey since
it's random what animal the player is.
"""
import logging
import sqlite3
from environment.grid import Tile
from environment.base_elements import Dirt
from environment.buildings import Zoo, create_zoo
from environment.liquids import Water
from organisms.animals import Animal, Elephant, Giraffe, Hyena, Lion, Rhino, Zebra
from organisms.organisms import LifeException
from organisms.plants import Bush, Grass, Tree

logging.disable(logging.CRITICAL)


def main():
    """
    This function is the main function of the game.
    """

    # create the zoo
    zoo = create_zoo(
        animals=[Elephant, Giraffe, Hyena, Lion, Rhino, Zebra],
        plants=[Bush, Grass, Tree],
    )

    zoo.refresh_grid()
    # print the zoo
    turn = 1
    zoo.elapsed_turns = 0
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
                if isinstance(thing, Tile):
                    thing = thing.type
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
                    zoo = Zoo.load_instance(thing.home_id)
                    zoo.reprocess_tiles()
                    action = thing.turn(turn_number=turn)
                    if action == "died":
                        dead_things.append(thing)
                except LifeException:
                    dead_things.append(thing)
                    # remove the animal from the grid
                    zoo.grid[thing.position[0]][thing.position[1]] = None
        turn += 1
        zoo.elapsed_turns += 1

        # logging.error(f"**********Turn {turn}**********")
        # logging.error(f"Zoo has {len(zoo.animals)} animals")
        #
        # logging.error(f"Zoo has {len(zoo.plants)} plants")
        # # if len(zoo.plants) > 100:
        # #     import pdb; pdb.set_trace()
        # #     pass
        # logging.error(f"Zoo has {len(zoo.water_sources)} water sources")

        zoo.check_full()
        # logging.error(f"Zoo is {'full' if zoo.full else 'not full'}")
        # input("Press enter to continue..")
        # clear the screen
        # redraw the grid
        print(f"Turn {turn}")
        zoo.refresh_grid()
        zoo = Zoo.load_instance(zoo.id)
        # input("Press enter to continue..")


# run the simulation
if __name__ == "__main__":
    main()
