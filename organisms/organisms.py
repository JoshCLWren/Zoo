"""
This module contains the base classes for all organisms.
"""

import logging
from uuid import uuid4

from faker import Faker

faker = Faker()


class Organism:
    """
    This is the base class for all organisms.
    """
    def __init__(self, home_id):
        """
        This method is called when an organism is created.
        :param home_id:
        """
        self.id = uuid4() # pylint: disable=invalid-name
        self.is_alive = True
        self.emoji = "🤷"
        self.name = faker.name()
        self.home_id = home_id
        self.title = f"{self.name} the {self.__class__.__name__}"
        self.cause_of_death = None

    def refresh_home_id(self, home_id):
        """
        This method refreshes the home id of the organism.
        :param home_id:
        :return:
        """
        self.home_id = home_id

    def __str__(self):
        """
        This method is called when an organism is printed.
        :return:
        """
        return self.title


class LifeException(Exception):
    """
    This is the base class for all life exceptions.
    """
    def __init__(self, animal):
        """
        This method is called when a life exception is created.
        :param animal:
        """
        self.animal = animal

    def __str__(self):
        """
        This method is called when a life exception is printed.
        :return:
        """
        logging.error("% has died", self.animal.title)
        return f"{self.animal.title} has died of {self.animal.cause_of_death}"
