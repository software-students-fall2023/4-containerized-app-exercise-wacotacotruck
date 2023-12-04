"""Module for Testing Python Functions"""
from unittest.mock import MagicMock, patch
import pytest
from bson import ObjectId
from werkzeug.security import generate_password_hash
from web_app.app import app
from web_app.app import cleanup


class Tests:
    """Test Functions for the Web App"""

    mock_user_id = str(ObjectId())

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

    @patch("web_app.app.s3")
    @patch("web_app.app.database")
    def test_cleanup(self, mock_db, mock_s3):
        """
        Test the cleanup function.
        """
        # Mock S3 bucket name as used in your application
        mock_s3_bucket_name = "voice2midi"

        # Mock S3 files
        mock_s3_files = [{"Key": "orphan_file.mid"}, {"Key": "linked_file.mid"}]
        mock_s3.list_objects_v2.return_value = {"Contents": mock_s3_files}

        # Mock MongoDB data
        mock_midi_collection = MagicMock()
        mock_midi_collection.find.return_value = [
            {
                "midi_url": f"https://{mock_s3_bucket_name}.s3.amazonaws.com/linked_file.mid"
            }
        ]
        mock_db.return_value = {"midis": mock_midi_collection}

        # Call the cleanup function
        result = cleanup()

        # Verify the result
        assert result == "cleanup completed"

        # Check that the delete_object method was called for the orphan file
        mock_s3.delete_object.assert_any_call(
            Bucket=mock_s3_bucket_name, Key="orphan_file.mid"
        )

    def test_upload_midi_user_not_logged_in(self, client):
        """Test uploading midi when user is not logged in."""
        response = client.post("/upload-midi", json={})
        assert response.status_code == 401
        assert response.json == {"error": "User not logged in"}

    def test_upload_midi_no_filename(self, client):
        """Test successful midi upload."""
        # Define a fixed mock ObjectId directly in the test
        fixed_mock_user_id = str(ObjectId("656d60f64ff92c523597e095"))

        # Mock session
        with client.session_transaction() as sess:
            sess["user_id"] = fixed_mock_user_id

        # Send POST request
        response = client.post("/upload-midi", json={})

        # Assert the response
        assert response.status_code == 400
        assert response.json == {"error": "No filename provided"}

    @patch("web_app.app.database_atlas.users.find_one")
    def test_upload_midi_user_not_found(self, mock_find_user, client):
        """Test successful midi upload."""
        # Define a fixed mock ObjectId directly in the test
        user_id = "656d60f64ff92c523597e095"

        # Mock session
        with client.session_transaction() as sess:
            sess["user_id"] = user_id

        mock_find_user.return_value = False

        # Send POST request
        response = client.post("/upload-midi", json={"filename": "test.mid"})

        # Assert the response
        assert response.status_code == 404
        assert response.json == {"error": "User not found"}

    # @patch("web_app.app.database")
    # def test_mymidi_user_logged_in(self, mock_db, client):
    #     """Test mymidi page when user is logged in."""
    #     mock_midi_collection = MagicMock()

    #     mock_midi_data = [
    #         {"user_id": self.mock_user_id, "midi_url": "http://example.com/midi1.mid"},
    #         {"user_id": self.mock_user_id, "midi_url": "http://example.com/midi2.mid"}
    #     ]

    #     mock_cursor = MagicMock()
    #     mock_cursor.sort.return_value = mock_midi_data
    #     mock_midi_collection.find.return_value = mock_cursor
    #     mock_db.return_value = {"midis": mock_midi_collection}

    #     # Mock user session
    #     with client.session_transaction() as session:
    #         session["user_id"] = self.mock_user_id

    #     response = client.get("/mymidi")
    #     assert response.status_code == 200
    #     assert all(midi['midi_url'] in str(response.data) for midi in mock_midi_data)

    def test_mymidi_user_not_logged_in(self, client):
        """Test mymidi page when user is not logged in."""
        # Ensure user_id is not in session
        with client.session_transaction() as session:
            session.pop("user_id", None)

        response = client.get("/mymidi")
        assert response.status_code == 200
        assert b"login.html" in response.data

    def test_signup_page(self, client):
        """Test that the signup page renders correctly"""
        response = client.get("/signup")
        assert response.status_code == 200
        assert b"Sign Up" in response.data

    @patch("web_app.app.database_atlas.users.find_one")
    def test_signup_with_existing_username(self, mock_find_one, client):
        """Test signup with an existing username"""

        mock_find_one.return_value = {"username": "existing_user"}
        
        new_user = {
            "username": "existing_user",
            "password": "Password123",
            "confirm_password": "Password123",
            "email": "exis_user@email.com",
        }

        # Ensure user_id is not in session
        with client.session_transaction() as session:
            session.pop("user_id", None) 

        response = client.post("/signup", data=new_user)

        assert response.status_code == 200
        assert b"Username already exists!" in response.data
    
    # @patch("web_app.app.database_atlas.users.find_one")
    # def test_signup_new_username(self, mock_find_one, client):
    #     """Test successful signup"""

    #     mock_find_one.return_value = None

    #     new_user = {
    #         "username": "newuser",
    #         "password": "Password123",
    #         "confirm_password": "Password123",
    #         "email": "new_user@email.com",
    #     }
    #     # Ensure user_id is not in session
    #     with client.session_transaction() as session:
    #         session.pop("user_id", None) 
            
    #     response = client.post("/signup", data=new_user, headers={"Content-Type": "application/json"})
    #     assert response.status_code == 200
    #     assert "/login" in response.headers["Location"]

    def test_login_user_logged_in(self, client):
        """Test login route when user is logged in."""
        with client.session_transaction() as session:
            session["user_id"] = "some_user_id"

        response = client.get("/login")

        assert response.status_code == 302
        assert '/' in response.headers['Location']

    def test_login_user_not_logged_in(self, client):
        """Test login route when user is not logged in."""
        with client.session_transaction() as session:
            session.pop("user_id", None)

        response = client.get("/login")

        assert response.status_code == 200
        assert b"login.html" in response.data
    
    def test_signup_password_too_short(self, client):
        """Test signup with a password that is too short"""
        data = {
            "username": "user",
            "password": "Zx25",
            "confirm_password": "Zx25",
            "email": "user@email.com",
        }
        response = client.post("/signup", data=data)
        assert response.status_code == 200
        assert b"Password must be between 8 and 20 characters long!" in response.data
    
    def test_signup_password_too_long(self, client):
        """Test signup with a password that is too long"""
        data = {
            "username": "user",
            "password": "PasswordPass12345678912345",
            "confirm_password": "PasswordPass12345678912345",
            "email": "user@email.com",
        }
        response = client.post("/signup", data=data)
        assert response.status_code == 200
        assert b"Password must be between 8 and 20 characters long!" in response.data
    
    def test_signup_password_no_digit(self, client):
        """Test signup with a password that has no digits"""
        data = {
            "username": "user",
            "password": "PassyPass",
            "confirm_password": "PassyPass",
            "email": "user@email.com",
        }
        response = client.post("/signup", data=data)
        assert response.status_code == 200
        assert b"Password should have at least one number!" in response.data

    def test_signup_password_no_alphabet(self, client):
        """Test signup with a password that has no alphabets"""
        data = {
            "username": "user",
            "password": "12345678",
            "confirm_password": "12345678",
            "email": "user@email.com",
        }
        response = client.post("/signup", data=data)
        assert response.status_code == 200
        assert b"Password should have at least one alphabet!" in response.data

    def test_login_auth_success(self, client):
        """Test successful login authentication."""
        # Prepare test data
        test_username = "test_user"
        test_password = "correct_password"

        # Mocking database call
        with patch("web_app.app.database_atlas.users.find_one") as mock_find_one, patch(
            "web_app.app.check_password_hash"
        ) as mock_check_password:
            # Mock the database response and password check
            mock_find_one.return_value = {
                "_id": ObjectId(),
                "username": test_username,
                "password": generate_password_hash(test_password),
            }
            mock_check_password.return_value = True

            # Simulate POST request
            response = client.post(
                "/login_auth",
                data={"username": test_username, "password": test_password},
            )

            # Assert redirection to index page
            assert response.status_code == 200

    def test_login_auth_failure(self, client):
        """Test login authentication with wrong credentials."""
        # Prepare test data with incorrect credentials
        test_username = "test_user"
        test_password = "wrong_password"

        # Mocking database call
        with patch("web_app.app.database_atlas.users.find_one") as mock_find_one, patch(
            "web_app.app.check_password_hash"
        ) as mock_check_password:
            # Mock the database response and password check
            mock_find_one.return_value = {
                "_id": ObjectId(),
                "username": test_username,
                "password": generate_password_hash("correct_password"),
            }
            mock_check_password.return_value = False

            # Simulate POST request
            response = client.post(
                "/login_auth",
                data={"username": test_username, "password": test_password},
            )

            # Assert that user is not redirected and error is shown
            assert response.status_code == 200
            assert b"Invalid username or password!" in response.data

    def test_forgot_password_get(self, client):
        """Test forgot password get"""
        try:
            # Send a GET request to the "/forgot_password" route
            response = client.get("/forgot_password")

            # Check if the response is None and raise an AssertionError if it is not
            assert response is None

        except TypeError as e:
            # Check if the TypeError message matches the expected message
            expected_message = (
                "The view function for 'forgot_password' did not return a valid response. "
                "The function either returned None or ended without a return statement."
            )
            assert str(e) == expected_message

    def test_forgot_password_post_invalid_input(self, client):
        """Test forgot password invalid input"""
        response = client.post(
            "/forgot_password",
            data={
                "username": "invalid_username",
                "password": "short",
                "confirm_password": "password_mismatch",
                "email": "invalid_email@example.com",
            },
        )

        assert response.status_code == 200

        assert b"Invalid username or email!" in response.data
        assert b"Password must be between 8 and 20 characters long!" in response.data
        assert b"Password should have at least one number!" in response.data
        # assert b"Password should have at least one alphabet!" in response.data
        # assert b"Passwords do not match!" in response.data

    def test_forgot_password_post_valid_input(self, client):
        """Test forgot password valid input"""
        valid_username = "valid_username"
        valid_password = "ValidPassword123"
        valid_email = "valid_email@example.com"

        response = client.post(
            "/forgot_password",
            data={
                "username": valid_username,
                "password": valid_password,
                "confirm_password": valid_password,
                "email": valid_email,
            },
        )

        # Check if the response redirects to another route (e.g., success page)
        assert response.status_code == 200  # HTTP status code for redirect

    def test_logout(self, client):
        """Test logout"""
        with client.session_transaction() as session:
            session["user_id"] = 123  # Replace with a valid user_id

        response = client.get("/logout")

        with client.session_transaction() as session:
            assert "user_id" not in session

        # Check if the response redirects to the "login" route
        assert response.status_code == 302  # HTTP status code for redirect
