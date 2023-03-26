"""
Test for the zoo module.
"""
from random import randint

import pytest
from organisms.animals import Elephant
from organisms.plants import Bush
from environment.buildings import create_zoo, zoo_schema_as_dict, create_zoo_table
import database
from environment.grid import Tile

class TestZooEntity:
    """
    Test the zoo entity.
    """

    def test_singleton(self):
        """
        Test that the zoo entity is a singleton.
        Ensure we aren't continually creating new zoos each turn.
        """
        db_connection = database.DatabaseConnection()
        db_connection.execute("SELECT * FROM zoos")
        zoo_count = db_connection.fetchall()
        zoo = create_zoo(
            animals=[Elephant],
            plants=[Bush],
            height=randint(10, 20),
            width=randint(10, 20),
        )
        db_connection.execute("SELECT * FROM zoos")
        new_zoo_count = db_connection.fetchall()
        assert len(new_zoo_count) == len(zoo_count) + 1
        first_visual = zoo.refresh_grid(visualise=True)
        for row in first_visual:
            for thing in row:
                assert not isinstance(thing, Tile)

        grid_deviations = 0
        turns = randint(1, 1000)
        print(f"Testing {turns} turns.")
        no_changes_in_output = 0
        for turn in range(turns):
            print(f"Turn {turn} of {turns}.")
            initial_grid = zoo.grid
            initial_grid_output = zoo.refresh_grid(visualise=True)
            for row in zoo.grid:
                for thing in row:
                    if isinstance(thing, Tile):
                        thing = thing.type
                        assert thing.home_id == zoo.id
                    if isinstance(thing, (Bush, Elephant)):
                        assert thing.home_id == zoo.id
                        thing.turn(turn_number=turn)
            latest_grid = zoo.refresh_grid(visualise=True)
            if latest_grid == initial_grid_output:
                no_changes_in_output += 1
            else:
                # print the diff
                for row in range(len(latest_grid)):
                    for column in range(len(latest_grid[row])):
                        if latest_grid[row][column] != initial_grid_output[row][column]:
                            print(
                                f"Diff at row {row}, column {column}: {initial_grid_output[row][column]} -> {latest_grid[row][column]}"
                            )

            db_connection.execute("SELECT * FROM zoos")
            zoo_count_post_turn = db_connection.fetchall()
            assert len(zoo_count_post_turn) == len(new_zoo_count)

            if initial_grid != zoo.grid:
                grid_deviations += 1

        expected_deviations = 0.5 * turns
        print(f"Grid deviations: {grid_deviations}")
        print(f"Expected deviations: {expected_deviations}")

        assert grid_deviations > int(expected_deviations)
        print(f"No changes in output: {no_changes_in_output} of {turns} turns.")
        assert no_changes_in_output != turns - 1

