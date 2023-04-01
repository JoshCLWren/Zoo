"""
Zoo is a game about what happens when the humans disappear and the animals take over.
The game is an overhead view of a zoo, where the player is given the role of one of the animals.
The goal is to survive as long as possible, and to do so the player must eat, sleep, and reproduce.
The player can also interact with other animals, and the player can also interact with the
environment. The player can be a carnivore, herbivore, or omnivore, and the player can be a
predator or prey since it's random what animal the player is.
"""

import logging
import sqlite3
import pygame



import database
from environment.base_elements import Dirt
from environment.buildings import Zoo, create_zoo
from environment.grid import Tile
from environment.liquids import Water
from organisms.animals import (Animal, Elephant, Giraffe, Hyena, Lion, Rhino,
                               Zebra)
from organisms.organisms import LifeException
from organisms.plants import Bush, Grass, Tree, Plant

#pylint: disable=line-too-long

logging.disable(logging.CRITICAL)
# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Define grid cell size and margin
CELL_SIZE = 50
MARGIN = 5

def main():
    """
    This function is the main function of the game.
    """
    # Initialize pygame
    pygame.init()


    db_connection = database.DatabaseConnection()
    # create the zoo
    try:
        simulate()
    except Exception as e:
        print(e)
        #print the stack trace
        import traceback
        traceback.print_exc()

        db_connection.close()
    except KeyboardInterrupt:
        print("Keyboard interrupt, closing database connection")
        db_connection.close()
    db_connection.close()


def simulate():
    """
    Simulate the zoo.
    :return:
    """
    zoo = create_zoo(
        animals=[Elephant, Giraffe, Hyena, Lion, Rhino, Zebra],
        plants=[Bush, Grass, Tree],
    )

    zoo.refresh_grid(visualise=False)
    # print the zoo
    turn = 1
    zoo.elapsed_turns = 0
    living_animals = 1
    while living_animals:
        # render the zoo
        simulate_with_pygame(zoo)
        import pdb; pdb.set_trace()
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
                    simulate_with_pygame(zoo)
                    action = thing.turn(turn_number=turn)
                    if action == "died":
                        dead_things.append(thing)
                except LifeException:
                    dead_things.append(thing)
                    # remove the animal from the grid
                    zoo.grid[thing.position[0]][thing.position[1]] = None
        turn += 1
        zoo.elapsed_turns += 1

        zoo.check_full()
        print(f"Turn {turn}")
        simulate_with_pygame(zoo)
        zoo = Zoo.load_instance(zoo.id)

def simulate_with_pygame(zoo):
    grid = zoo.refresh_grid(visualise=False)

    # Set up the display
    screen = pygame.display.set_mode(
        ((CELL_SIZE + MARGIN) * len(grid[0]) + MARGIN, (CELL_SIZE + MARGIN) * len(grid) + MARGIN)
    )

    pygame.display.set_caption("Zoo Simulation")

    # Main pygame loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Draw grid
        for row in range(len(grid)):
            for column in range(len(grid[0])):
                color = WHITE
                cell = grid[row][column]

                # Set color based on the type of object
                if isinstance(cell, Tile):
                    cell = cell.type
                if isinstance(cell, (Water, Dirt)):
                    color = BLUE
                elif isinstance(cell, Plant):
                    color = GREEN
                elif isinstance(cell, Animal):
                    color = RED


                pygame.draw.rect(
                    screen,
                    color,
                    [
                        (MARGIN + CELL_SIZE) * column + MARGIN,
                        (MARGIN + CELL_SIZE) * row + MARGIN,
                        CELL_SIZE,
                        CELL_SIZE,
                    ],
                )

        # Update the screen
        pygame.display.flip()

    # Quit pygame
    pygame.quit()



# run the simulation
if __name__ == "__main__":
    main()
