import random
import uuid


class Water:
    """
    This is the class for water on the map.
    """

    def __init__(self, position=None, home_id=None, id=str(uuid.uuid4())):
        """
        This method is called when the water is created.
        """
        if position is None:
            position = [0, 0]
        self.position = position
        self.size = random.randint(1, 5)
        self.emoji = "🌊"
        self.home_id = home_id
        self.id = id
