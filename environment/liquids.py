import random


class Water:
    """
    This is the class for water on the map.
    """

    def __init__(self):
        """
        This method is called when the water is created.
        """
        self.position = [0, 0]
        self.size = 1
        self.emoji = "🌊"
