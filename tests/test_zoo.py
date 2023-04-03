"""
Test for the zoo module.
"""
from random import randint

import pytest

import database
from environment.buildings import (create_zoo, create_zoo_table,
                                   zoo_schema_as_dict)
from environment.grid import Tile
from organisms.animals import Elephant
from organisms.plants import Bush


class TestZooEntity:
    """
    Test the zoo entity.
    """

    @pytest.fixture(scope="class", autouse=True)
    def db_connection(self):
        """
        Create a database connection.
        """
        db_connection = database.DatabaseConnection()
        yield db_connection
        db_connection.close()

    def test_singleton(self, db_connection):
        """
        Test that the zoo entity is a singleton.
        Ensure we aren't continually creating new zoos each turn.
        """
        db_connection.execute("SELECT * FROM zoos")
        zoo_count = db_connection.fetchall()
        self.test_zoo()
        db_connection.execute("SELECT * FROM zoos")
        new_zoo_count = db_connection.fetchall()
        assert len(new_zoo_count) == len(zoo_count) + 1

    def test_zoo_turn(self, db_connection):
        zoo = self.test_zoo()
        db_connection.execute("SELECT * FROM zoos")
        new_zoo_count = db_connection.fetchall()
        first_visual = zoo.refresh_grid(visualise=True)
        for row in first_visual:
            for thing in row:
                assert not isinstance(thing, Tile)

        grid_deviations = 0
        # turns = randint(1, 1000)
        turns = 10
        print(f"Testing {turns} turns.")
        no_changes_in_output = 0
        elephant_moves = 0
        for turn in range(turns):
            (
                elephant_moves,
                grid_deviations,
                no_changes_in_output,
            ) = self.take_a_test_turn(
                elephant_moves,
                grid_deviations,
                no_changes_in_output,
                turn,
                turns,
                zoo,
                new_zoo_count,
            )

        expected_deviations = 0.5 * turns
        print(f"Grid deviations: {grid_deviations}")
        print(f"Expected deviations: {expected_deviations}")

        assert grid_deviations > int(expected_deviations)
        print(f"No changes in output: {no_changes_in_output} of {turns} turns.")
        assert no_changes_in_output != turns - 1
        assert elephant_moves > 0

    def take_a_test_turn(
        self,
        elephant_moves,
        grid_deviations,
        no_changes_in_output,
        turn,
        turns,
        zoo,
        new_zoo_count,
    ):
        db_connection = database.DatabaseConnection()
        print(f"Turn {turn} of {turns}.")
        initial_grid = zoo.grid
        initial_grid_output = zoo.refresh_grid(visualise=True)
        self.check_things_in_grid(turn, zoo)
        latest_grid = zoo.refresh_grid(visualise=True)
        if latest_grid == initial_grid_output:
            no_changes_in_output += 1
        else:
            # print the diff
            elephant_moves = self.check_row_diffs(
                elephant_moves, initial_grid_output, latest_grid
            )
        db_connection.execute("SELECT * FROM zoos")
        zoo_count_post_turn = db_connection.fetchall()
        assert len(zoo_count_post_turn) == len(new_zoo_count)
        if initial_grid != zoo.grid:
            grid_deviations += 1
        return elephant_moves, grid_deviations, no_changes_in_output

    def check_row_diffs(self, elephant_moves, initial_grid_output, latest_grid):
        for row in range(len(latest_grid)):
            for column in range(len(latest_grid[row])):
                if latest_grid[row][column] != initial_grid_output[row][column]:
                    print(
                        f"Diff at row {row}, column {column}: {initial_grid_output[row][column]} -> {latest_grid[row][column]}"
                    )
                    if isinstance(latest_grid[row][column], Elephant):
                        elephant_moves += 1
        return elephant_moves

    def check_things_in_grid(self, turn, zoo):
        for row in zoo.grid:
            for thing in row:
                if isinstance(thing, Tile):
                    thing = thing.type
                    assert thing.home_id == zoo.id
                if isinstance(thing, (Bush, Elephant)):
                    assert thing.home_id == zoo.id
                    thing.turn(turn_number=turn)

    def test_zoo(self):
        return create_zoo(
            animals=[Elephant],
            plants=[Bush],
            height=randint(10, 20),
            width=randint(10, 20),
        )

    def test_zoo_duplicate_animals(self):
        """
        Test that the zoo isn't duplicating animals.
        """
        zoo = self.test_zoo()
        db = database.DatabaseConnection()
        db.execute("SELECT * FROM animals")
        animal_count = len(db.fetchall())
        zoo.refresh_grid(visualise=True)
        for turn in range(10):
            for row in zoo.grid:
                for thing in row:
                    if isinstance(thing, Elephant):
                        thing.turn(turn_number=turn)
            zoo.refresh_grid(visualise=True)
        db.execute("SELECT * FROM animals")
        new_animal_count = len(db.fetchall())
        assert new_animal_count == animal_count
