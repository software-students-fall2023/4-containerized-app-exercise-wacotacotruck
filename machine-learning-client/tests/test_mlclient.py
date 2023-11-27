"""Module for Testing Python Functions"""
import pytest


class Tests:
    """Test Functions for the Machine Learning Client"""

    @pytest.fixture
    def example_fixture(self):
        """An example of a pytest fixture"""
        yield

    # Test functions
    def test_sanity_check(self):
        """Run a simple test for mlclient side that always passes."""
        expected = True
        actual = True
        assert actual == expected, "Expected it to always be True!"