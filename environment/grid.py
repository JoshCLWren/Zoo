"""
A grid is made up of tiles. Each tile represents a square in the 2d grid.
Each tile has a type, which is one of the following:
    - Dirt
    - Water
    - Plant
    - Animal
    - None
Each tile has a position, which is a list of two integers.
Each tile has a home_id, which is a string uuid4.
"""
import uuid

from database import DatabaseConnection


class TileError(Exception):
    """
    This is the exception for tiles.
    """

    pass


def create_tiles_table(conn):
    """
    This method creates the table for the tile.
    """
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS tiles (
            id TEXT PRIMARY KEY NOT NULL,
            x_position INTEGER NOT NULL,
            y_position INTEGER NOT NULL,
            home_id TEXT NOT NULL,
            type TEXT NOT NULL
        );
        """
        conn.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)
        conn.rollback()


class Tile:
    """
    This is the class for tiles. Which are the building blocks of the grid.
    """

    def __init__(self, position, home_id, _type):
        """
        This method is called when a tile is created.
        """
        self.position = position
        self.home_id = home_id
        self.type = _type
        self.id = str(uuid.uuid4())
        self.db = DatabaseConnection()

    def __str__(self):
        """
        This method is called when a tile is printed.
        """
        return "Tile"

    def save(self):
        """
        This method saves the tile to the database.
        """
        # check if the tile already exists

        x_position = self.position[0]
        y_position = self.position[1]

        try:
            if loaded_tile := Tile.load(self.home_id, self.position):
                # update the tile
                self.id = loaded_tile.id
                self.position = [x_position, y_position]
                self.update()
        except TileError as e:
            sql = """
                    INSERT INTO tiles (x_position, y_position, home_id, type, id) VALUES (?, ?, ?, ?, ?)
                    """
            try:
                self.db.conn.execute(
                    sql, (x_position, y_position, self.home_id, self.type, self.id)
                )
                self.db.conn.commit()
            except TileError as e:
                print(e)
                self.db.conn.rollback()

    @classmethod
    def load(cls, home_id, position=None):
        """
        This method loads the tile from the database.
        """
        db = DatabaseConnection()
        if position:
            x_position = position[0]
            y_position = position[1]
            sql = """
            SELECT * FROM tiles WHERE x_position=? AND y_position=? AND home_id=?
            """
            try:
                db.cur = db.conn.cursor()
                db.cur.execute(sql, (x_position, y_position, home_id))
                rows = db.cur.fetchall()
            except TileError as e:
                print(e)
                db.conn.rollback()
                return None
            if not rows:
                print("No rows found")
                return None
            row = rows[0]
            tile = cls([row[1], row[2]], row[3], row[4])
            tile.id = row[0]
            return tile
        else:
            sql = """
            SELECT * FROM tiles WHERE home_id=?
            """
            try:
                cur = db.conn.cursor()
                db.cur.execute(sql, (home_id,))
                rows = db.cur.fetchall()
            except TileError as e:
                print(e)
                db.conn.rollback()
                return None
            if not rows:
                print("No rows found")
                return None
            tiles = []
            for row in rows:
                tile = cls([row[1], row[2]], row[3], row[4])
                tile.id = row[0]
                tiles.append(tile)
            return tiles

    def update(self):
        """
        This method updates the tile in the database.
        """
        x_position = self.position[0]
        y_position = self.position[1]
        sql = """
        UPDATE tiles SET x_position=?, y_position=?, home_id=?, type=? WHERE id=?
        """
        try:
            self.db.conn.execute(
                sql, (x_position, y_position, self.home_id, self.type, self.id)
            )
            self.db.conn.commit()
        except TileError as e:
            print(e)
            self.db.conn.rollback()
