"""
Tests for the behaviour of organisms.
"""

import organisms.organisms


class TestOrganisms:
    """
    Class for tests around the behaviour of Organism objects.
    """

    def test_organisms_have_ids(self):
        """
        Test that organisms have ids.
        """
        organism = organisms.organisms.Organism()
        assert organism.id is not None