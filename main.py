"""
Zoo is a game about what happens when the humans disappear and the animals take over.
The game is an overhead view of a zoo, where the player is given the role of one of the animals.
The goal is to survive as long as possible, and to do so the player must eat, sleep, and reproduce.
The player can also interact with other animals, and the player can also interact with the
environment. The player can be a carnivore, herbivore, or omnivore, and the player can be a
predator or prey since it's random what animal the player is.
"""
from organisms.animals import Animal, Elephant, Giraffe, Hyena, Lion, Rhino, Zebra

import logging
import sqlite3

import pygame

import database
from environment.base_elements import Dirt
from environment.buildings import Zoo, create_zoo
from environment.grid import Tile
from environment.liquids import Water
from organisms.organisms import LifeException
from organisms.plants import Bush, Grass, Plant, Tree

# pylint: disable=line-too-long

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
        # print the stack trace
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
    zoo = Zoo.load_instance(zoo.id)
    flat_list = [element for sublist in zoo.grid for element in sublist]
    living_animals = [item for item in flat_list if isinstance(item, Animal)]
    living_animals = len(living_animals)
    turn = 0
    print(f"Starting with {living_animals} animals")
    while living_animals:

        zoo.refresh_grid(visualise=False)
        # print the zoo
        turn, living_animals = simulate_with_pygame(zoo, turn)
        print(f"Turn {turn} with {living_animals} animals")



def take_turn(turn, zoo):
    zoo = Zoo.load_instance(zoo.id)
    flat_list = [element for sublist in zoo.grid for element in sublist]
    living_animals = [item for item in flat_list if isinstance(item, Animal)]
    living_animals = len(living_animals)
    if not living_animals:
        return False

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
    return zoo.refresh_grid(visualise=False)
def simulate_with_pygame(zoo, turn=1, living_animals=1):
    zoo.elapsed_turns = turn
    grid = zoo.refresh_grid(visualise=False)

    # Set up the display
    screen = pygame.display.set_mode(
        (
            (CELL_SIZE + MARGIN) * len(grid[0]) + MARGIN,
            (CELL_SIZE + MARGIN) * len(grid) + MARGIN,
        )
    )

    pygame.display.set_caption("Zoo Simulation")
    zoo = Zoo.load_instance(zoo.id)
    take_turn(turn, zoo)
    # Draw grid
    for row in range(len(grid)):
        for column in range(len(grid[0])):
            cell_content = grid[row][column]
            asset = "images/Dirt.png"
            if cell_content == "🐘":
                asset = "images/Elephant.png"
            elif cell_content == "🦒":
                asset = "images/Giraffe.png"
            elif cell_content == "🦓":
                asset = "images/Zebra.png"
            elif cell_content == "🦏":
                asset = "images/Rhino.png"
            elif cell_content == "🦁":
                asset = "images/Lion.png"
            elif cell_content == "🌿":
                asset = "images/Grass.png"
            elif cell_content == "🌳":
                asset = "images/Tree.png"
            elif cell_content == "🌊":
                asset = "images/Water.png"
            elif cell_content == "🦡":
                asset = "images/Hyena.png"

            # draw the asset in the square of the grid
            image = pygame.image.load(asset)
            image = pygame.transform.scale(image, (CELL_SIZE, CELL_SIZE))
            screen.blit(image, (MARGIN + (CELL_SIZE + MARGIN) * column, MARGIN + (CELL_SIZE + MARGIN) * row + 50))

        # Update the screen
        pygame.display.flip()

        # take a turn
        grid = take_turn(turn, zoo)
        if not grid:
            break
        turn += 1
        living_animals = len([item for item in grid if isinstance(item, Animal)])
        return turn, living_animals





# run the simulation
if __name__ == "__main__":
    main()
