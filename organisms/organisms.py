from uuid import uuid4
from faker import Faker

faker = Faker()


class Organism:
    def __init__(self):
        self.id = uuid4()
        self.is_alive = True
        self.emoji = "🤷"
        self.name = faker.name()


class LifeException(Exception):
    def __init__(self, animal):
        self.animal = animal

    def __str__(self):
        logging.error(f"{self.animal.name} has died")
        return f"{self.animal.name} has died"
