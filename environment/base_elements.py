"""
This file contains the base elements of the environment.
These are the elements that are not animals or plants or water or buildings.
"""

import uuid
from assets import GameAsset
class Dirt(GameAsset):
    """
    This is the class for dirt.
    """

    def __init__(self, position=None, home_id=None, id=str(uuid.uuid4())):
        """
        This method is called when dirt is created.
        """
        super().__init__()
        if position is None:
            position = [0, 0]
        self.size = 1
        self.nutrients = 0
        self.position = position
        self.emoji = "🪨 "
        self.home_id = home_id
        self.id = id

    def __str__(self):
        """
        This method is called when dirt is printed.
        """

        return "Dirt"
