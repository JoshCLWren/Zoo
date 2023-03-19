import contextlib
import datetime
import itertools
import logging
import pickle
import random
import sqlite3
import uuid
from dataclasses import dataclass, field

import arrow
import pandas as pd

import database
import environment.grid
from environment.base_elements import Dirt
from environment.grid import Tile, create_tiles_table
from environment.liquids import Water
from organisms.animals import (Animal, Elephant, Giraffe, Hyena, Lion, Rhino,
                               Zebra)
from organisms.dead_things import Corpse
from organisms.plants import Bush, Grass, Tree


def make_blank_grid(height, width):
    """
    This method creates a blank grid for the zoo.
    :return:
    """
    return [[None for _ in range(height)] for _ in range(width)]


class ZooError(Exception):
    """
    This is the exception for the zoo.
    """

    pass


@dataclass
class Zoo:
    """
    This is the class for the zoo.
    """

    _instance = None

    def __init__(self, height: int, width: int):
        """
        This method is called when the zoo is created.
        """
        now = arrow.now().isoformat()
        self.full: bool = False
        self.height: int = 0
        self.width: int = 0
        self.id: str = str(uuid.uuid4())
        self.csv_path: str = f"zoo_{self.id}.csv"
        self.created_dt: str = now
        self.updated_dt: str = now
        self.is_raining: bool = False
        self.water_sources: list = []
        self.tiles_to_refresh: list = []
        self.grid: list = []
        self.height = height
        self.width = width
        # grid is a matrix of the same size as the zoo
        # it contains the string representation of the animal at that position
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.elapsed_turns: int = 0
        self.db = database.DatabaseConnection()

    @classmethod
    def load_instance(cls, zoo_id):
        """
        This method loads a Zoo instance from the database.
        """
        if cls._instance is not None:
            return cls._instance
        db = database.DatabaseConnection()
        conn = db.conn
        print("Loading the zoo from the database...")
        df = pd.read_sql_query(
            "SELECT * FROM zoos WHERE id = ?", conn, params=(zoo_id,)
        )
        if df.empty:
            raise ZooError("No zoo found with that ID.")
        # create a dictionary from the DataFrame
        zoo_dict = df.to_dict(orient="records")[0]
        # deserialize the string representations of the lists
        grid = make_blank_grid(zoo_dict["height"], zoo_dict["width"])
        with contextlib.suppress(sqlite3.OperationalError):  # tiles might not exist yet
            if tiles := Tile.load(conn, zoo_id):
                for tile in tiles:
                    grid[tile.position[0]][tile.position[1]] = tile
        zoo_dict["grid"] = grid
        zoo = cls(height=zoo_dict["height"], width=zoo_dict["width"])
        for key, value in zoo_dict.items():
            setattr(zoo, key, value)
        return zoo

    def refresh_from_db(self):
        """
        This method queries the database for the latest version of the zoo.
        And updates the attributes of the instance.
        :param conn:
        :return:
        """
        self._instance = None
        self._instance = self.load_instance(zoo_id=self.id)

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

    def __str__(self):
        """
        This method is called when the zoo is printed.
        """

        return "Zoo"

    def refresh_grid(self, visualise=True):
        """
        This method is called when the grid is updated.
        :param visualise: whether to print the grid to the console
        :param conn: the database connection
        """
        self.refresh_from_db()
        # check self.tiles_to_refresh and replace the tiles with what they were before an animal moved
        # to that tile
        for key, value in self.__dict__.items():
            if key in [
                "animals",
                "plants",
                "water_sources",
                "tiles_to_refresh",
            ] and isinstance(value, str):
                value = value.split(",")
            if value == "[]":
                value = []

            setattr(self, key, value)
        tiles = {
            "animals": database.Entity.load_all("animals", self.id),
            "plants": database.Entity.load_all("plants", self.id),
            "water_sources": database.Entity.load_all("water", self.id),
            "dirt": database.Entity.load_all("dirt", self.id),
        }

        grid = make_blank_grid(self.height, self.width)
        if not tiles:
            # if there are no tiles yet then there is no need to refresh the grid
            raise ZooError("No tiles found in the database.")
        for value in tiles.values():
            for entity in value:
                # unpickle the tile
                instance = pickle.load(open(entity["pickled_instance"], "rb"))
                grid[instance.position[0]][instance.position[1]] = instance

        self.grid = grid
        self.reprocess_tiles()
        intensity, is_raining = self.weather()
        # fill any vacant tiles with dirt
        self.fill_blanks(intensity, is_raining)
        self._instance = None
        self._instance = self.load_instance(zoo_id=self.id)

        # print the emoji representation of the grid to the console, with each row on a new line
        # print the grid to the console in the form of a matrix
        # center the grid in the console
        if visualise:
            for row in self.grid:
                print("".join([cell.emoji for cell in row]))

    def weather(self):
        self.is_raining = random.choice([True, False])
        intensity = None
        if self.is_raining:
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
        return intensity, self.is_raining

    def fill_blanks(self, intensity=None, is_raining=False):
        """
        This method fills any vacant tiles with dirt or grass.
        :param intensity: the intensity of the rain
        :param is_raining: if it is raining
        :return: None
        """

        # iterate through the rows and colums of the grid preventing any off by one errors
        for i in range(self.width):
            for j in range(self.height):
                if self.grid[i][j] is None:
                    if is_raining:
                        self.make_puddle(i, j, random.randint(1, 10))
                    else:
                        self.grid[i][j] = Dirt()
                        self.grid[i][j].position = (i, j)
                        self.grid[i][j].size = random.randint(1, 10)

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
        try:
            north_neighbour = self.grid[i - 1][j] if i > 0 else None
        except IndexError:
            north_neighbour = None
        try:
            south_neighbour = self.grid[i + 1][j] if i < self.height - 1 else None
        except IndexError:
            south_neighbour = None
        try:
            east_neighbour = self.grid[i][j + 1] if j < self.width - 1 else None
        except IndexError:
            east_neighbour = None
        try:
            west_neighbour = self.grid[i][j - 1] if j > 0 else None
        except IndexError:
            west_neighbour = None
        try:
            north_east_neighbour = (
                self.grid[i - 1][j + 1] if i > 0 and j < self.width - 1 else None
            )
        except IndexError:
            north_east_neighbour = None

        try:
            north_west_neighbour = self.grid[i - 1][j - 1] if i > 0 and j > 0 else None
        except IndexError:
            north_west_neighbour = None
        try:
            south_east_neighbour = (
                self.grid[i + 1][j + 1]
                if i < self.height - 1 and j < self.width - 1
                else None
            )
        except IndexError:
            south_east_neighbour = None
        try:
            south_west_neighbour = (
                self.grid[i + 1][j - 1] if i < self.height - 1 and j > 0 else None
            )
        except IndexError:
            south_west_neighbour = None

        return {
            "north": north_neighbour,
            "south": south_neighbour,
            "east": east_neighbour,
            "west": west_neighbour,
            "north_east": north_east_neighbour,
            "north_west": north_west_neighbour,
            "south_east": south_east_neighbour,
            "south_west": south_west_neighbour,
        }

    def reprocess_tiles(self):
        tiles_to_refresh = []
        # remove and None values from self.tiles_to_refresh
        self.tiles_to_refresh = [
            tile for tile in self.tiles_to_refresh if tile is not None
        ]
        if self.tiles_to_refresh == ["[]"]:
            return self
        for tile in self.tiles_to_refresh:
            # check if the tile is occupied by an animal
            # try to deserialize the tile from a string i.e. '[<environment.grid.Tile object at 0x12928b450>'
            if isinstance(tile, str):
                for bracket in ("[", "]"):
                    tile = tile.replace(bracket, "")
                tile = tile.split(", ")
                deserialized_tile = []
                for item in tile:
                    item = item.replace("<", "")

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

    def save_instance(self, zoo_entity):
        """
        This method saves the instance of the Zoo to the database.
        :return:
        """

        zoo_entity._instance = None
        zoo_entity.height = self.height
        zoo_entity.width = self.width
        zoo_entity.save()


def create_zoo(height=35, width=65, options=None, animals=None, plants=None):
    """
    This function creates the zoo.
    """
    # get the system width and height

    if options is None:
        options = ["animal", "plant", "water"]
    zoo = Zoo(height=height, width=width)
    columns_and_types = {
        "id": "TEXT PRIMARY KEY",
        "height": "INTEGER",
        "width": "INTEGER",
        "created_dt": "TEXT",
        "updated_dt": "TEXT",
    }
    zoo_table = database.Table(table_name="zoos", columns_and_types=columns_and_types)
    zoo_table.create_table()
    zoo_entity = database.Entity(
        table_name="zoos",
        list_of_values=[
            zoo.id,
            zoo.height,
            zoo.width,
            zoo.created_dt,
            zoo.updated_dt,
        ],
        columns_and_types=columns_and_types,
    )
    inserted_zoo = zoo_entity.insert()
    zoo = zoo.load_instance(inserted_zoo["id"])
    tile_schema = {
        "id": "TEXT PRIMARY KEY",
        "occupied": "BOOLEAN",
        "position": "TEXT",
        "home_id": "TEXT",
        "type": "TEXT",
        "created_dt": "TEXT",
        "updated_dt": "TEXT",
    }
    tile_table = database.Table(table_name="tiles", columns_and_types=tile_schema)
    tile_table.create_table()

    water_limit = 0.1 * height * width
    water_placed = 0
    animal_instances = []
    plant_instances = []
    water_instances = []
    dirt_instances = []

    # fill the zoo with random animals
    empty_grid_tiles = zoo.height * zoo.width
    for row, column in itertools.product(range(width), range(height)):
        selection = random.choice(options)
        try:
            if selection == "animal":
                if empty_grid_tiles > 0:
                    empty_grid_tiles -= 1
                    animal = random.choice(animals)
                    animal = animal(home_id=zoo.id)
                    animal.position = [row, column]
                    zoo.grid[row][column] = animal
                    tile = environment.grid.Tile(
                        position=[row, column], home_id=zoo.id, _type=animal
                    )
                    zoo.tiles_to_refresh.append(tile)
                    animal_instances.append(animal)
            elif selection == "plant":
                if empty_grid_tiles > 0:
                    empty_grid_tiles -= 1
                    plant = random.choice(plants)
                    plant = plant(home_id=zoo.id)
                    plant.position = [row, column]
                    zoo.grid[row][column] = plant
                    tile = environment.grid.Tile(
                        position=[row, column], home_id=zoo.id, _type=plant
                    )
                    zoo.tiles_to_refresh.append(tile)
                    plant_instances.append(plant)
            elif selection == "water" and not water_placed > water_limit:
                if empty_grid_tiles > 0:
                    empty_grid_tiles -= 1
                    water_id = str(uuid.uuid4())
                    water = Water(home_id=zoo.id, position=[row, column], id=water_id)
                    zoo.grid[row][column] = water
                    water_placed += 1
                    tile = environment.grid.Tile(
                        position=[row, column], home_id=zoo.id, _type=water
                    )
                    zoo.tiles_to_refresh.append(tile)
                    water_instances.append(water)
            else:
                dirt_id = str(uuid.uuid4())
                dirt = Dirt(position=[row, column], home_id=zoo.id, id=dirt_id)
                zoo.grid[row][column] = dirt

                tile = environment.grid.Tile(
                    position=[row, column], home_id=zoo.id, _type=dirt
                )
                zoo.tiles_to_refresh.append(tile)
                dirt_instances.append(dirt)
        except IndexError:
            continue
    db = database.DatabaseConnection()
    for key, value in {
        "animals": animal_instances,
        "plants": plant_instances,
        "water": water_instances,
        "dirt": dirt_instances,
    }.items():
        batch_insert(key, value, zoo, db)

    zoo.save_instance(zoo_entity)
    zoo = zoo.load_instance(zoo.id)

    return zoo


def batch_insert(table_name, zoo_list, zoo, db):
    # create the water
    _schema = {
        "id": "TEXT PRIMARY KEY",
        "home_id": "TEXT REFERENCES zoos(id)",
        "pickled_instance": "BLOB",
        "created_dt": "TEXT",
        "updated_dt": "TEXT",
    }
    table = database.Table(table_name=table_name, columns_and_types=_schema)
    batch = []
    table.create_table()
    for item in zoo_list:
        # pickle the water
        _id = str(item.id)
        _pickle = pickle.dumps(item)
        _entity = database.Entity(
            table_name=table_name,
            list_of_values=[
                _id,
                zoo.id,
                _pickle,
            ],
            columns_and_types=_schema,
        )
        batch.append(_entity)
    db.insert_many(table_name=table_name, entities=batch)
