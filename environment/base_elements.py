class Dirt:
    """
    This is the class for dirt.
    """

    def __init__(self, position=None, home_id=None):
        """
        This method is called when dirt is created.
        """
        if position is None:
            position = [0, 0]
        self.size = 1
        self.nutrients = 0
        self.position = position
        self.emoji = "🪨 "
        self.home_id = home_id

    def __str__(self):
        """
        This method is called when dirt is printed.
        """

        return "Dirt"
