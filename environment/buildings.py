import contextlib
import datetime
import itertools
import logging
import random
import uuid
from dataclasses import dataclass, field

import arrow
import pandas as pd

from environment.base_elements import Dirt
from environment.liquids import Water
from organisms.animals import Animal, Elephant, Giraffe, Hyena, Lion, Rhino, Zebra
from organisms.dead_things import Corpse
from organisms.plants import Bush, Grass, Tree


@dataclass
class Zoo:
    """
    This is the class for the zoo.
    """

    def __init__(self, height: int, width: int):
        """
        This method is called when the zoo is created.
        """
        self.full: bool = False
        self.height: int = 0
        self.width: int = 0
        self.id: str = str(uuid.uuid4())
        self.csv_path: str = f"zoo_{self.id}.csv"
        self.created_dt: str = arrow.now().isoformat()
        self.updated_dt: str = arrow.now().isoformat()
        self.is_raining: bool = False
        self.animals: list = []
        self.plants: list = []
        self.water_sources: list = []
        self.tiles_to_refresh: list = []
        self.grid: list = []
        self.height = height
        self.width = width
        # grid is a matrix of the same size as the zoo
        # it contains the string representation of the animal at that position
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.elapsed_turns: int = 0

    def create_table(self, conn):
        """
        This method creates the database table for the zoo.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS zoos (
                            id TEXT PRIMARY KEY,
                            height INTEGER,
                            width INTEGER,
                            full INTEGER,
                            created_dt TEXT,
                            updated_dt TEXT,
                            is_raining BOOLEAN,
                            animals TEXT,
                            plants TEXT,
                            water_sources TEXT,
                            tiles_to_refresh TEXT
                            grid TEXT
                            )"""
            )
            conn.commit()
        except Exception as e:
            print(e)
            conn.rollback()

    def save(self, conn):
        """
        This method saves the zoo to the sqlite database..
        It will upsert the zoo if it already exists.
        :param conn: the connection to the database
        """
        print(f"Saving the zoo to the database... zoo_id = {self.id}")

        self.updated_dt = arrow.now().isoformat()
        # create a string representation of the grid
        grid_str = "\n".join(
            [",".join([str(cell) for cell in row]) for row in self.grid]
        )
        # create a dictionary from the attributes of the class instance
        zoo_dict = self.__dict__
        grid_copy = zoo_dict["grid"]
        # add the string representation of the grid to the dictionary
        zoo_dict["grid_str"] = grid_str
        # remove the nested list representation of the grid from the dictionary
        del zoo_dict["grid"]
        self.grid = grid_copy
        # create the table if it does not exist
        self.create_table(conn)
        # insert the zoo into the database
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO 
                    zoos
                    (   
                        id, 
                        height, 
                        width, 
                        full, 
                        created_dt, 
                        updated_dt, 
                        is_raining, 
                        animals, 
                        plants, 
                        water_sources, 
                        tiles_to_refresh, 
                        grid
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.id,
                    self.height,
                    self.width,
                    int(self.full),
                    self.created_dt,
                    self.updated_dt,
                    int(self.is_raining),
                    str(self.animals),
                    str(self.plants),
                    str(self.water_sources),
                    str(self.tiles_to_refresh),
                    grid_str,
                ),
            )
            conn.commit()
        except Exception as e:
            print(e)
            conn.rollback()

    @classmethod
    def load(cls, conn):
        """
        This method loads a Zoo instance from the database.
        """
        # load the DataFrame from the CSV file
        print("Loading the zoo from the database...")
        df = pd.read_sql_query("SELECT * FROM zoos WHERE id = ?", conn, params=(id,))
        # create a dictionary from the DataFrame
        zoo_dict = df.to_dict(orient="records")[0]
        # deserialize the string representations of the lists
        for key, value in zoo_dict:
            if key in ["animals", "plants", "water_sources", "tiles_to_refresh"]:
                zoo_dict[key] = value.split(",")
            if key == "grid":
                zoo_dict[key] = value.split("\n")
                zoo_dict[key] = [
                    [cell for cell in row.split(",")] for row in zoo_dict[key]
                ]
        return cls(**zoo_dict)

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
        This method is called when the grid is updated.
        :param visualise: whether to print the grid to the console
        """
        self.update_from_csv()
        # check self.tiles_to_refresh and replace the tiles with what they were before an animal moved
        # to that tile

        self.reprocess_tiles()
        intensity, is_raining = self.weather()
        # fill any vacant tiles with dirt
        self.fill_blanks(intensity, is_raining)
        # update the save_as_csv of the zoo
        self.save_as_csv()

        # print the emoji representation of the grid to the console, with each row on a new line
        # print the grid to the console in the form of a matrix
        # center the grid in the console
        if visualise:
            for row in self.grid:
                print("".join([cell.emoji for cell in row]))

    def weather(self):
        self.is_raining = random.choice([True, False])
        intensity = None
        if is_raining:
            intensities = {
                "torrential": 0.01,
                "heavy": 0.05,
                "moderate": 0.9,
                "mist": 0.1,
            }
            intensity = random.choices(
                list(intensities.keys()), weights=list(intensities.values())
            )[0]
            print(f"It is raining {intensity}.")
        return intensity, is_raining

    def fill_blanks(self, intensity=None, is_raining=False):
        """
        This method fills any vacant tiles with dirt or grass.
        :param intensity: the intensity of the rain
        :param is_raining: if it is raining
        :return: None
        """
        for i in range(self.height):
            for j in range(self.width):
                if self.grid[i][j] is None:
                    # check if the tile is next to water and if so make it grass
                    neighbors = self.tiles_neighbors(i, j)
                    for neighbor in neighbors.values():
                        if (
                            neighbor
                            and neighbor.__class__ == Water
                            or neighbor.__class__ == Grass
                        ):
                            self.grid[i][j] = Grass(self)
                            self.grid[i][j].position = (i, j)
                            break
                    else:
                        self.grid[i][j] = Dirt()
                        self.grid[i][j].position = (i, j)
                if is_raining:
                    self.rain(i, j, intensity)

    def make_puddle(self, x, y, water_size):
        self.grid[x][y] = Water()
        self.grid[x][y].position = (x, y)
        self.grid[x][y].size = water_size

    def rain(self, i, j, intensity):
        """
        This method is called when it is raining.
        :param i: The x coordinate of the tile
        :param j: The y coordinate of the tile
        :param intensity: The intensity of the rain
        :return:
        """
        if (
            self.grid[i][j].__class__ == Water and intensity == "mist"
        ) and random.choice([True, False]):
            self.grid[i][j].size += random.randint(1, 10)
        if (
            self.grid[i][j].__class__ == Dirt and intensity == "moderate"
        ) and random.choice([True, False]):
            self.grid[i][j] = Water()
            self.grid[i][j].position = (i, j)
            self.grid[i][j].size = random.randint(1, 10)
        if (
            self.grid[i][j].__class__ == Dirt and intensity == "heavy"
        ) and random.choice([True, False]):
            self.make_puddle(i, j, 50)
        if self.grid[i][j].__class__ == Dirt and intensity == "torrential":
            self.make_puddle(i, j, 75)
        if (
            self.grid[i][j].__class__ == Grass and intensity == "torrential"
        ) and random.choice([True, False]):
            self.make_puddle(i, j, 20)
        if (
            self.grid[i][j].__class__ == Water and intensity == "torrential"
        ) and random.choice([True, False]):
            self.grid[i][j].size += random.randint(1, 20)

    def tiles_neighbors(self, i, j):
        north_neighbour = self.grid[i - 1][j] if i > 0 else None
        south_neighbour = self.grid[i + 1][j] if i < self.height - 1 else None
        east_neighbour = self.grid[i][j + 1] if j < self.width - 1 else None
        west_neighbour = self.grid[i][j - 1] if j > 0 else None
        north_east_neighbour = (
            self.grid[i - 1][j + 1] if i > 0 and j < self.width - 1 else None
        )
        north_west_neighbour = self.grid[i - 1][j - 1] if i > 0 and j > 0 else None
        south_east_neighbour = (
            self.grid[i + 1][j + 1]
            if i < self.height - 1 and j < self.width - 1
            else None
        )
        south_west_neighbour = (
            self.grid[i + 1][j - 1] if i < self.height - 1 and j > 0 else None
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
        return neighbors

    def reprocess_tiles(self):
        tiles_to_refresh = []
        # remove and None values from self.tiles_to_refresh
        self.tiles_to_refresh = [
            tile for tile in self.tiles_to_refresh if tile is not None
        ]
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
        return self


def create_zoo(conn, height=35, width=65, options=None, animals=None, plants=None):
    """
    This function creates the zoo.
    """
    # get the system width and height

    if options is None:
        options = ["animal", "plant", "water"]
    zoo = Zoo(height=height, width=width)
    zoo.save(conn)
    path_to_csv = zoo.csv_path
    water_limit = 0.1 * height * width
    water_placed = 0

    # fill the zoo with random animals
    empty_grid_tiles = zoo.height * zoo.width
    for row, column in itertools.product(range(height), range(width)):
        selection = random.choice(options)
        zoo = Zoo.load_from_csv(path_to_csv)
        if selection == "animal":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                animal = random.choice(animals)
                animal = animal(home_id=zoo.id)
                animal.position = [row, column]
                zoo.add_animal(animal)
                zoo.grid[row][column] = animal
        elif selection == "plant":
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                plant = random.choice(plants)
                plant = plant(home_id=zoo.id)
                plant.position = [row, column]
                zoo.add_plant(plant)
                zoo.grid[row][column] = plant
        elif selection == "water" and not water_placed > water_limit:
            if empty_grid_tiles > 0:
                empty_grid_tiles -= 1
                water = Water(home_id=zoo.id, position=[row, column])
                zoo.add_water(water)
                zoo.grid[row][column] = water
                water_placed += 1
        else:
            dirt = Dirt(position=[row, column], home_id=zoo.id)
            zoo.grid[row][column] = dirt
        zoo.save_as_csv()
    return zoo
