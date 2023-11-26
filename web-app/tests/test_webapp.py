"""Module for Testing Python Functions"""
import pytest

class Tests:
    """Test Functions for the Web App"""

    @pytest.fixture
    def example_fixture(self):
        """An example of a pytest fixture"""
        yield

    # Test functions
    def test_sanity_check(self):
        """Run a simple test that always passes."""
        expected = True
        actual = True
        assert actual == expected, "Expected True to be equal to True!"
