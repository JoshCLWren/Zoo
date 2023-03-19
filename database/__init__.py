"""
Singleton patterns for database connection and cursors and error handling and entities.
"""

import sqlite3
import uuid

import arrow


class DatabaseError(Exception):
    """
    This is the class for database errors.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class DatabaseConnection:
    """
    This class is a singleton for the database connection.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            print("Creating the database connection...")
            cls._instance = super(DatabaseConnection, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, database_name="zoo.db"):
        try:
            self.conn = sqlite3.connect(database_name)
            self.cur = self.conn.cursor()
        except DatabaseError as e:
            print(e)

    def execute(self, sql, params=None):
        """
        This method executes the sql statement.
        """
        try:
            if params:
                self.cur.execute(sql, params)
            else:
                self.cur.execute(sql)
            self.conn.commit()
        except DatabaseError as e:
            print(e)
            self.conn.rollback()

    def fetchall(self):
        """
        This method fetches all the rows.
        """
        return self.cur.fetchall()

    def fetchone(self):
        """
        This method fetches one row.
        """
        return self.cur.fetchone()

    def close(self):
        """
        This method closes the connection.
        """
        self.conn.close()

    def drop(self, database_name="zoo.db"):
        """
        This method drops the database.
        """
        # find the tables in the database
        sql = """
        SELECT name FROM sqlite_master WHERE type='table'
        """
        try:
            self._attempt_drop(sql, database_name)
        except DatabaseError as e:
            print(e)
            self.conn.rollback()

    def _attempt_drop(self, sql, database_name):
        """
        This method attempts to drop the database.
        :param sql: the sql statement
        :param database_name: the name of the database
        :return:
        """
        self.execute(sql)
        rows = self.fetchall()
        # drop the tables
        for row in rows:
            sql = f"""
                DROP TABLE {row[0]}
                """
            self.execute(sql)
        # drop the database
        sql = f"""
            DROP DATABASE {database_name}
            """
        self.execute(sql)
        self.close()

    def insert_many(self, table_name, entities):
        """
        This method inserts many entities into the database.
        :param table_name: the name of the table
        :param entities: the entities to insert
        """
        print(f"Inserting many {table_name} entities into the database...")
        # get the columns
        columns = entities[0].columns
        _values = [
            entity.get_values(dt_override=arrow.now().isoformat())
            for entity in entities
        ]

        sql = f"""
            INSERT INTO {table_name} VALUES ({','.join(['?' for _ in range(len(columns))])})
        """
        self.cur.executemany(sql, _values)
        self.conn.commit()


class Table:
    """
    This is the base class for tables.
    """

    def __init__(self, table_name=None, foreign_keys=None, columns_and_types=None):
        """
        This method initializes the table.
        :param table_name: the name of the table
        :param columns: the columns of the table
        :param foreign_keys: the foreign keys of the table
        """
        columns = []
        types = []
        if columns_and_types:
            for column, _type in columns_and_types.items():
                columns.append(column)
                types.append(_type)
        if table_name is None:
            raise ValueError("The table name cannot be None.")
        if foreign_keys is None:
            foreign_keys = {}

        self.table_name: str = table_name
        self.columns: tuple = tuple(columns)
        self.foreign_keys: dict = foreign_keys
        self.db: DatabaseConnection = DatabaseConnection()
        self.sanitized_columns: str = None
        self.sanitized_foreign_keys: str = None
        self.columns_types: tuple = tuple(types)

    def create_table(self):
        """
        This method creates the table in the database.
        """
        if len(self.columns) != len(self.columns_types):
            raise ValueError(
                "The number of columns must be equal to the number of columns types."
            )
        sql = f"CREATE TABLE IF NOT EXISTS {self.table_name} ("
        for column, _type in zip(self.columns, self.columns_types):
            sql += f"{column} {_type}, "
        sql = sql[:-2]
        sql += ")"
        if self.foreign_keys:
            sql += " "
            sql += self.sanitized_foreign_keys

        try:
            self.db.execute(sql)
            return True
        except sqlite3.DatabaseError as e:
            print(e)
            return False

    def create_foreign_keys(self):
        """
        This method creates the foreign keys in the database.
        """
        for key, value in self.foreign_keys.items():
            sql = f"ALTER TABLE {self.table_name} ADD FOREIGN KEY "
            sql += "%(key)s REFERENCES %(value)s"
            try:
                self.db.execute(sql, {"key": key, "value": value})
                return True
            except DatabaseError as e:
                print(e)
                return False

    def values_placeholder(self):
        """
        This method sanitizes the columns and foreign keys.
        """
        self.sanitized_columns = ",".join(self.columns)
        sanitized_values = ",".join(["?" for _ in range(len(self.columns))])
        if self.foreign_keys:
            self.sanitized_foreign_keys = ",".join(self.foreign_keys.keys())
        return sanitized_values


class Entity(Table):
    """
    This is the base class for entities.
    """

    def __init__(
        self,
        id=None,
        table_name=None,
        list_of_values=None,
        foreign_keys=None,
        columns_and_types=None,
    ):
        """
        This method initializes the entity.
        :param id: the id of the entity
        :param table_name: the name of the table
        :param columns: the columns of the table
        :param list_of_values: the values of the entity
        :param foreign_keys: the foreign keys of the entity
        """
        super(Entity, self).__init__(
            table_name=table_name,
            foreign_keys=foreign_keys,
            columns_and_types=columns_and_types,
        )
        self.id: str = id
        self.list_of_values: list = list_of_values
        self.db: DatabaseConnection = DatabaseConnection()
        self.sanitized_columns: str = None
        self.sanitized_values: str = None

    def __dict__(self):
        """
        This method returns the entity as a dictionary.
        """
        return self.dict_response()

    def save(self):
        """
        This method saves the entity to the database.
        """
        self.db = DatabaseConnection()
        self.values_placeholder()
        # first try to insert the entity
        if self.id is None:
            try:
                self.insert()
                return True
            except sqlite3.IntegrityError:
                # if the entity already exists, update it
                self.update()
                return True
            except sqlite3.DatabaseError as e:
                print(e)
                return False
        else:
            try:
                self.update()
                return True
            except sqlite3.DatabaseError as e:
                print(e)
                return False

    @classmethod
    def load(cls, id):
        """
        This method loads the entity from the database.
        """
        sql = f"""
        SELECT * FROM {cls.table_name} WHERE id=%s(id)s
        """
        try:
            self.db.execute(sql, [id])
            row = self.db.fetchone()
            return cls(*row)
        except DatabaseError as e:
            print(e)
            return False

    @classmethod
    def load_all(cls, table_name, foreign_key):
        """
        This method loads all the entities from the database related to the foreign key.
        :param table_name:
        :param foreign_key:
        :return: a list of entities
        """
        sql = f"""
        SELECT * FROM {table_name} WHERE home_id = ?
        """
        try:
            db = DatabaseConnection()
            db.execute(sql, [foreign_key])
            rows = db.fetchall()
            return [cls(*row) for row in rows]
        except DatabaseError as e:
            print(e)
            return False

    def update(self, columns_to_update=None, values_to_update=None):
        """
        This method updates the entity in the database.
        """
        if columns_to_update:
            if len(columns_to_update) != len(values_to_update):
                raise ValueError(
                    "The number of columns to update must be equal to the number of values to update."
                )
            sql = f"INSERT INTO {self.table_name}"
            sql_columns = "".join(
                f" %s({columns_to_update[i]})s," for i in range(len(columns_to_update))
            )
            sql_values = "".join(
                f" %s({values_to_update[i]})s," for i in range(len(values_to_update))
            )
            sql_columns = sql_columns[:-1]  # remove the last comma
            sql_values = sql_values[:-1]  # remove the last comma
            sql += f"({sql_columns}) VALUES ({sql_values})"
            try:
                self.db.execute(sql, values_to_update)
                return True
            except DatabaseError as e:
                print(e)
                return False
        else:
            self.id = self.list_of_values[0]
            sql = f"UPDATE {self.table_name} SET "
            non_id_columns = self.columns[1:]
            non_id_values = self.list_of_values[1:]
            sql += "".join(f" {column}=?," for column in non_id_columns)
            sql = sql[:-1]  # remove the last comma
            sql += f" WHERE id = '{self.id}'"

            try:
                self.db.execute(sql, non_id_values)
                return True
            except DatabaseError as e:
                print(e)
                return False

    def delete(self):
        """
        This method deletes the entity from the database.
        """
        if not self.id:
            raise ValueError("The entity must have an id to be deleted.")
        sql = f"DELETE FROM {self.table_name} WHERE id=%s(id)s"
        try:
            self.db.execute(sql, [self.id])
            return True
        except DatabaseError as e:
            print(e)
            return False

    def insert(self):
        """
        This method inserts the entity into the database.
        """
        placeholders = self.values_placeholder()

        sql = f"""
        INSERT INTO {self.table_name} ({self.sanitized_columns}) VALUES ({placeholders})
        """
        try:
            _values = (*self.list_of_values,)
            self.db.execute(sql, _values)
            return self.dict_response()
        except DatabaseError as e:
            print(e)
            return False

    def dict_response(self):
        """
        This method returns a dictionary response.
        """
        response = {"id": self.id}
        for i in range(len(self.columns)):
            response[self.columns[i]] = self.list_of_values[i]
        return response

    def get_values(self, dt_override=False):
        """
        This method returns the values of the entity as a tuple to be used in executemany method.
        :return: the values of the entity as a tuple
        """
        _values = [self.id, *self.list_of_values] if self.id else self.list_of_values
        if dt_override:
            # add values to be used for created_dt and updated_dt as the value of the passed dt_override
            # for each value the the end of the list
            _values.extend([dt_override, dt_override])
        return tuple(_values)
