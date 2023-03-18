class Dirt:
    """
    This is the class for dirt.
    """

    def __init__(self):
        """
        This method is called when dirt is created.
        """
        self.size = 0
        self.nutrients = 0
        self.position = [0, 0]
        self.emoji = "🪨 "

    def __str__(self):
        """
        This method is called when dirt is printed.
        """

        return "Dirt"
