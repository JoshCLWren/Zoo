from uuid import uuid4

from faker import Faker
import logging
faker = Faker()


class Organism:
    def __init__(self, home_id):
        self.id = uuid4()
        self.is_alive = True
        self.emoji = "🤷"
        self.name = faker.name()
        self.home_id = home_id
        self.title = f"{self.name} the {self.__class__.__name__}"
        self.cause_of_death = None

    def refresh_home_id(self, home_id):
        self.home_id = home_id


class LifeException(Exception):
    def __init__(self, animal):
        self.animal = animal

    def __str__(self):
        logging.error(f"{self.animal.name} has died")
        return f"{self.animal.title} has died of {self.animal.cause_of_death}"
