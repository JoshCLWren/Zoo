"""
Tests for the behaviour of organisms.
"""
import environment.buildings
import organisms.organisms


class TestOrganisms:
    """
    Class for tests around the behaviour of Organism objects.
    """

    def test_organisms_have_ids(self, mock_zoo):
        """
        Test that organisms have ids.
        """
        x_pos, y_pos = 0, 0

        organism = organisms.organisms.Organism(home_id=mock_zoo.id)
        organism.position = [x_pos, y_pos]
        mock_zoo.grid[x_pos][y_pos] = organism
        assert organism.id is not None
