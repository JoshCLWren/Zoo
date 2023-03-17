from uuid import uuid4


class Organism:
    def __init__(self):
        self.id = uuid4()
        self.is_alive = True


class LifeException(Exception):
    def __init__(self, animal):
        self.animal = animal

    def __str__(self):
        return f"{self.__str__()} has died"
