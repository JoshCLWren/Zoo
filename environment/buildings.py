import contextlib
import datetime
import io
import itertools
import os
import pickle
import platform
import random
import sqlite3
import time
import uuid
from dataclasses import dataclass, field

import arrow

import database
import environment.grid
from environment.base_elements import Dirt
from environment.grid import Tile, create_tiles_table
from environment.liquids import Water
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

    def __init__(self, height: int, width: int, id: str = None):
        """
        This method is called when the zoo is created.
        """
        now = arrow.now().isoformat()
        self.full: bool = False
        self.height: int = 0
        self.width: int = 0
        self.id: str = str(uuid.uuid4()) if id is None else id
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
    def load_instance(cls, zoo_id: str):
        """
        This method loads a Zoo instance from the database.
        """
        if not isinstance(zoo_id, str) and isinstance(zoo_id, Zoo):
            zoo_id = zoo_id.id

        if cls._instance is not None:
            return cls._instance
        db = database.DatabaseConnection()
        conn = db.conn
        df = pd.read_sql_query(
            "SELECT * FROM zoos WHERE id = ?", conn, params=(zoo_id,)
        )

        if df.empty:
            raise ZooError("No zoo found with that ID.")
        # create a dictionary from the DataFrame
        zoo_dict = df.to_dict(orient="records")[0]
        # deserialize the string representations of the lists
        grid = cls.get_all_zoos_things(
            zoo_id=zoo_id, height=zoo_dict["height"], width=zoo_dict["width"]
        )
        if zoo_dict.get("id"):
            zoo = cls(
                id=zoo_dict["id"], height=zoo_dict["height"], width=zoo_dict["width"]
            )
        else:
            zoo = cls(height=zoo_dict["height"], width=zoo_dict["width"])
        zoo.grid = grid
        for key, value in zoo_dict.items():
            if key == "grid":
                continue
            setattr(zoo, key, value)

        cls._instance = zoo
        return zoo

    def refresh_from_db(self):
        """
        This method queries the database for the latest version of the zoo.
        And updates the attributes of the instance.
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
        for row in self.grid:
            for cell in row:
                # check if the cell is empty or Dirt
                if cell is None or isinstance(cell, Dirt):
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
        param visualise: bool - whether to print the grid to the console or not (default: True).
        :return:
        """
        self.reprocess_tiles()
        self.refresh_from_db()

        intensity, is_raining = self.weather()
        self.fill_blanks(intensity)
        self._instance = None
        self._instance = self.load_instance(zoo_id=self.id)

        grid = []

        # Clear the console screen
        # os.system("cls" if platform.system().lower() == "windows" else "clear")

        for row in self.grid:
            row_emojis = []
            for cell in row:
                if isinstance(cell, Tile):
                    row_emojis.append(cell.type.emoji)
                else:
                    row_emojis.append(cell.emoji)
            grid.append(row_emojis)
            if visualise:
                print("".join([cell for cell in row_emojis]))

        # Add a small delay to control the refresh rate (optional)
        # time.sleep(0.1)

        return grid

    @staticmethod
    def get_all_zoos_things(zoo_id: str, height: int, width: int):
        """
        Load all the things in the zoo from the database.
        :return: a list of all the things in the zoo
        """
        zoo_tiles_schema = {
            "id": "TEXT PRIMARY KEY",
            "home_id": "TEXT REFERENCES zoos(id)",
            "pickled_instance": "BLOB",
            "created_dt": "TEXT",
            "updated_dt": "TEXT",
        }
        try:
            animals = database.Entity.load_all(
                "animals", zoo_id, schema=zoo_tiles_schema
            )
        except sqlite3.OperationalError:
            animals = []
        try:
            plants = database.Entity.load_all("plants", zoo_id, schema=zoo_tiles_schema)
        except sqlite3.OperationalError:
            plants = []
        try:
            water_sources = database.Entity.load_all(
                "water", zoo_id, schema=zoo_tiles_schema
            )
        except sqlite3.OperationalError:
            water_sources = []
        try:
            dirt = database.Entity.load_all("dirt", zoo_id, schema=zoo_tiles_schema)
        except sqlite3.OperationalError:
            dirt = []
        tiles = {
            "animals": animals,
            "plants": plants,
            "water_sources": water_sources,
            "dirt": dirt,
        }
        grid = make_blank_grid(height, width)
        if not tiles:
            # if there are no tiles yet then there is no need to refresh the grid
            raise ZooError("No tiles found in the database.")
        # find any tiles that share the same position and replace them with the latest version

        for value in tiles.values():
            for entity in value:
                if entity.get("pickled_instance") is None:
                    continue
                value = entity.get("pickled_instance")
                file_data = io.BytesIO(value)
                tile = pickle.load(file_data)
                if grid[tile.position[0]][tile.position[1]] is None:
                    grid[tile.position[0]][tile.position[1]] = tile
                else:
                    current_tile = grid[tile.position[0]][tile.position[1]]
                    current_tile_from_db = database.Entity.load(
                        id=current_tile.id,
                        table_name=current_tile.__class__.__name__.lower(),
                    )
                    tile_from_db = database.Entity.load(
                        id=tile.id, table_name=tile.__class__.__name__.lower()
                    )
                    if current_tile_from_db["updated_dt"] < tile_from_db["updated_dt"]:
                        most_recent_tile = tile
                    else:
                        most_recent_tile = current_tile
                    grid[tile.position[0]][tile.position[1]] = most_recent_tile
        return grid

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

    def fill_blanks(self, is_raining=False):
        """
        This method fills any vacant tiles with dirt or grass.
        param is_raining: if it is raining
        :return: None
        """

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
        """
        This method reprocesses the tiles that have been changed.
        :return:
        """
        new_tiles_to_refresh = []
        tiles_to_remove = []

        for tile in self.tiles_to_refresh:
            if tile is None:
                tiles_to_remove.append(tile)
                continue

            if isinstance(tile, Tile):
                tile = tile.type

            # Check if the cell is an instance of an Animal
            if issubclass(
                self.grid[tile.position[0]][tile.position[1]].__class__, Animal
            ):
                # If it is, replace the tile with the animal
                self.grid[tile.position[0]][tile.position[1]] = tile
            else:
                # If it isn't, add it to the list of tiles to refresh
                new_tiles_to_refresh.append(tile)

        # Remove any None values from self.tiles_to_refresh
        for tile in tiles_to_remove:
            self.tiles_to_refresh.remove(tile)

        # Replace the old list with the new one
        self.tiles_to_refresh = new_tiles_to_refresh

    def save_instance(self):
        """
        This method saves the instance of the Zoo to the database.
        :return:
        """
        load_id = self.id or None
        self._instance = None
        columns_to_update = zoo_schema_as_dict()
        columns_to_update.pop("id")
        updated_values = {}
        for key, value in columns_to_update.items():
            value = getattr(self, key)
            updated_values[key] = value
        # updated_values["id"] = self.id
        list_of_values = [val for val in updated_values.values()]
        if updated_zoo := database.Entity(
            columns_and_types=columns_to_update,
            list_of_values=list_of_values,
            table_name="zoos",
        ):
            updated_zoo.save(load_id=load_id)
            self.refresh_from_db()
            return self
        else:
            return None


def create_zoo(height=20, width=20, options=None, animals=None, plants=None):
    """
    This function creates the zoo.
    """
    # get the system width and height

    if options is None:
        options = ["animal", "plant", "water"]
    zoo = Zoo(height=height, width=width)
    zoo, zoo_entity = zoo_database_operations(zoo)

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
                empty_grid_tiles = make_animal(
                    animal_instances, animals, column, empty_grid_tiles, row, zoo
                )
            elif selection == "plant":
                if empty_grid_tiles > 0:
                    empty_grid_tiles = make_plant(
                        column, empty_grid_tiles, plant_instances, plants, row, zoo
                    )
            elif selection == "water" and not water_placed > water_limit:
                if empty_grid_tiles > 0:
                    empty_grid_tiles, water_placed = make_water(
                        column,
                        empty_grid_tiles,
                        row,
                        water_instances,
                        water_placed,
                        zoo,
                    )
            else:
                make_dirt(column, dirt_instances, row, zoo)
        except IndexError:
            continue
    insert_zoos_occupants(
        animal_instances, dirt_instances, plant_instances, water_instances, zoo
    )
    zoo.save_instance()
    return zoo.load_instance(zoo.id)


def insert_zoos_occupants(
    animal_instances, dirt_instances, plant_instances, water_instances, zoo
):
    db = database.DatabaseConnection()
    for key, value in {
        "animals": animal_instances,
        "plants": plant_instances,
        "water": water_instances,
        "dirt": dirt_instances,
    }.items():
        if value:
            batch_insert(key, value, zoo, db)


def make_dirt(column, dirt_instances, row, zoo):
    dirt_id = str(uuid.uuid4())
    dirt = Dirt(position=[row, column], home_id=zoo.id, id=dirt_id)
    dirt.process_image()
    zoo.grid[row][column] = dirt
    tile = environment.grid.Tile(position=[row, column], home_id=zoo.id, _type=dirt)
    zoo.tiles_to_refresh.append(tile)
    dirt_instances.append(dirt)


def make_water(column, empty_grid_tiles, row, water_instances, water_placed, zoo):
    empty_grid_tiles -= 1
    water_id = str(uuid.uuid4())
    water = Water(home_id=zoo.id, position=[row, column], id=water_id)
    water.process_image()
    zoo.grid[row][column] = water
    water_placed += 1
    tile = environment.grid.Tile(position=[row, column], home_id=zoo.id, _type=water)
    zoo.tiles_to_refresh.append(tile)
    water_instances.append(water)
    return empty_grid_tiles, water_placed


def make_plant(column, empty_grid_tiles, plant_instances, plants, row, zoo):
    empty_grid_tiles -= 1
    plant = random.choice(plants)
    plant = plant(home_id=zoo.id)
    plant.process_image()
    plant.position = [row, column]
    zoo.grid[row][column] = plant
    tile = environment.grid.Tile(position=[row, column], home_id=zoo.id, _type=plant)
    zoo.tiles_to_refresh.append(tile)
    plant_instances.append(plant)
    return empty_grid_tiles


def make_animal(animal_instances, animals, column, empty_grid_tiles, row, zoo):
    if empty_grid_tiles > 0:
        empty_grid_tiles -= 1
        animal = random.choice(animals)
        animal = animal(home_id=zoo.id)
        animal.process_image()
        animal.position = [row, column]
        zoo.grid[row][column] = animal
        tile = environment.grid.Tile(
            position=[row, column], home_id=zoo.id, _type=animal
        )
        zoo.tiles_to_refresh.append(tile)
        animal_instances.append(animal)
    return empty_grid_tiles


def zoo_database_operations(zoo):
    columns_and_types = zoo_schema_as_dict()
    create_zoo_table(columns_and_types)
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
    return zoo, zoo_entity


def zoo_schema_as_dict():
    """
    :return: a dictionary of the zoo schema
    """
    return {
        "id": "TEXT PRIMARY KEY",
        "height": "INTEGER",
        "width": "INTEGER",
        "created_dt": "TEXT",
        "updated_dt": "TEXT",
    }


def create_zoo_table(columns_and_types):
    zoo_table = database.Table(table_name="zoos", columns_and_types=columns_and_types)
    zoo_table.create_table()


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
