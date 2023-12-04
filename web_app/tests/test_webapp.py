"""Module for Testing Python Functions"""
from unittest.mock import MagicMock
import pytest
from web_app.app import app


class Tests:
    """Test Functions for the Web App"""

    @pytest.fixture
    def example_fixture(self):
        """An example of a pytest fixture for"""
        yield

    @pytest.fixture
    def mocker(self):
        """Mocker fixture"""
        return MagicMock()

    # Test functions
    def test_sanity_check(self):
        """Run a simple test for the webapp side that always passes."""
        actual = True
        expected = True
        assert actual == expected, "Expected True to be equal to True!"

    @pytest.fixture
    def client(self):
        """Test client for web app"""
        app.config["TESTING"] = True
        with app.test_client() as test_client:
            yield test_client

    def test_index_route(self, client):
        """Test index route"""
        response = client.get("/")
        assert response.status_code == 200

    def test_browse_route(self, client, mocker):
        """Test browse route"""
        # Mock data that you expect to retrieve from MongoDB
        mock_midi_data = [
            {
                "_id": {"$oid": "656cfc3617ebc67b1a462aa1"},
                "user_id": "6564ccca7dabd39ef5b760af",
                "username": "ao",
                "midi_url": "https://voice2midi.s3.amazonaws.com/output_d860b6d9-fbfec98f1bc1.mid",
            },
            {
                "_id": {"$oid": "656d04cb26e9fb093236c26a"},
                "user_id": "6564ccca7dabd39ef5b760af",
                "username": "ao",
                "midi_url": "https://voice2midi.s3.amazonaws.com/output_abbc1ef7-f250f8d3eb.mid",
            },
        ]

        midi_collection_mock = mocker.MagicMock()
        midi_collection_mock.find.return_value = mock_midi_data

        with mocker.patch('web_app.app.database["midis"]', midi_collection_mock):
            response = client.get("/browse")

        assert response.status_code == 200
