class Corpse:
    """
    This is the class for dead animals.
    """

    def __init__(self, former_animal=None):
        """
        This method is called when the dead animal is created.
        """
        self.former_animal = former_animal.__str__()
        self.nutrients = former_animal.size + former_animal.virility
        self.size = former_animal.size
        self.position = former_animal.position
        self.emoji = "💀"

    def decompose(self):
        """
        This method is called when the dead animal decomposes.
        """

        self.size -= 1
        self.nutrients -= 1

    def turn(self, *args, **kwargs):
        """
        This method is called when the dead animal turns.
        """

        self.decompose()
        return 'decomposed'
