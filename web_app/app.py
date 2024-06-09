"""Web-app."""
import os

import logging
from datetime import datetime
from flask import Flask, url_for, redirect, render_template, session, request, jsonify

# import requests
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

import boto3
from bson import ObjectId
from botocore.exceptions import ClientError
from flask_session import Session

# Initializes Flask application and loads the .env file from the MongoDB Atlas Database
app = Flask(__name__)
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Initialize S3 client - commented out for now due to pylint
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
s3_bucket_name = os.getenv("S3_BUCKET_NAME")

host = os.getenv("HOST", "localhost")

s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
)

# Monitors Flask's session management: Uses a secret key to sign and encrypt session data
# Secret key is essential for the proper functioning of user sessions in your Flask application.
# Used when users sign into their account, it creates a private session for them (security reasons)
sess = Session()
app.secret_key = os.getenv("APP_SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
sess.init_app(app)

# Establish a database connection with the MONGO_URI (MongoDB Atlas connection)
client_atlas = MongoClient(os.getenv("MONGO_URI"))

# Checks if the connection has been made, else make an error printout
try:
    client_atlas.admin.command("ping")
    database_atlas = client_atlas[os.getenv("MONGO_DBNAME")]
    print("* Connected to MongoDB!")
except ConnectionError as err:
    print('* "Failed to connect to MongoDB at', os.getenv("MONGO_URI"))
    print("Database connection error:", err)

# except Exception as err:
#     print('* "Failed to connect to MongoDB at', os.getenv("MONGO_URI"))
#     print("Database connection error:", err)

# Connect to MongoDB
client = MongoClient("db", 27017)
database = client["database"]


# Routes
@app.route("/")
def index():
    """Renders the home page"""
    if "user_id" in session:
        user_id = session.get("user_id")
        return render_template("index.html", user_id=user_id)
    return render_template("index.html")


@app.route("/browse")
def browse():
    """Renders the browse page"""
    midi_collection = database_atlas["midis"]
    midi_posts = midi_collection.find({}).sort("created_at", -1)
    return render_template("browse.html", midi_posts=list(midi_posts))


def cleanup():
    """Function to cleanup S3"""
    try:
        midi_urls = set()
        if "midis" in database.list_collection_names():
            midi_collection = database["midis"]
            midi_urls = {midi["midi_url"] for midi in midi_collection.find()}

        s3_files = s3.list_objects_v2(Bucket=s3_bucket_name).get("Contents", [])
        s3_urls = {
            f"https://{s3_bucket_name}.s3.amazonaws.com/{file['Key']}"
            for file in s3_files
        }

        orphan_files = s3_urls - midi_urls

        for url in orphan_files:
            key = url.split("/")[-1]
            s3.delete_object(Bucket=s3_bucket_name, Key=key)
            # app.logger.info(f"Deleted orphan file: {url}")

        return "cleanup completed"
    except ClientError as e:
        logging.error("ClientError during S3 operation: %s", e)
        return str(e)


@app.route("/upload-midi", methods=["POST"])
def upload_midi():
    """Handles uploading midi to the database."""
    if "user_id" not in session:
        app.logger.warning("User not logged in")
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    filename = data.get("filename")

    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    user_id = session["user_id"]

    try:
        user_id_obj = ObjectId(user_id)
    except TypeError:
        return jsonify({"error": "Invalid User ID"}), 400

    user = database_atlas.users.find_one({"_id": user_id_obj})

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Format the S3 URL
    s3_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{filename}"

    # Save the S3 URL with user details
    midi_collection = database_atlas["midis"]
    midi_data = {
        "user_id": user_id,
        "username": user["username"],
        "midi_url": s3_url,
        "created_at": datetime.utcnow(),
    }
    midi_collection.insert_one(midi_data)

    return jsonify({"message": "MIDI URL uploaded successfully"}), 200


# Allowing users to see their own midis here
@app.route("/mymidi", methods=["GET", "POST"])
def mymidi():
    """Renders the mymidi page"""
    if "user_id" in session:
        midi_collection = database["midis"]

        # Retreive user_id from session
        user_id = session["user_id"]

        # Find the MIDI files belonging to the user
        user_posts = midi_collection.find({"user_id": user_id}).sort("created_at", -1)
        # user_id_obj = ObjectId(user_id)
        # user_posts = midi_collection.find({"user_id": user_id_obj}).sort("created_at", -1)
        return render_template("mymidi.html", user_posts=list(user_posts))
    return render_template("login.html")


# def call_ml_client(data):
#     """Contacts the ml client"""
#     if "user_id" in session:
#         data["user_id"] = session.get("user_id")
#         # logging.info("Sending data to ML Client:", data)
#         response = requests.post("http://localhost:5002/process", json=data, timeout=10)
#         return response.json()
#     # else:
#     #     logging.info("User not logged in.")
#     return "Log in first!"


# def call_ml_client(data):
#     """Contacts the ml client"""
#     response = requests.post("http://localhost:5002/process", json=data, timeout=10)
#     return response.json()


# This is the function which registers the signup page from the login.html page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Renders the signup page"""
    # If there is a user_id in session, it redirects them back to the home page
    if "user_id" in session:
        return redirect(url_for("index"))

    # If there is no account, then we allow the user to creat one.
    if request.method == "POST":
        # We allow the user to create their username, password, confirm password, email
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        email = request.form["email"]
        errors = []

        # This checks if there is already a user that has this exact username
        if database_atlas.users.find_one({"username": username}):
            errors.append("Username already exists!")

        # This checks if there is already a user that has this exact email
        if database_atlas.users.find_one({"email": email}):
            errors.append("Email already used, try another or try logging in!")

        # This checks if the password is in between 8-20 characters
        if not 8 <= len(password) <= 20:
            errors.append("Password must be between 8 and 20 characters long!")

        # This checks if the password does not have any numbers
        if not any(char.isdigit() for char in password):
            errors.append("Password should have at least one number!")

        # This checks if the password does not have any alphabets
        if not any(char.isalpha() for char in password):
            errors.append("Password should have at least one alphabet!")

        # This checks if the password and the confirm password do not match
        if not confirm_password == password:
            errors.append("Passwords do not match!")

        # If any errors, it will re-render the signup.html page and allow the user to try again
        if errors:
            return render_template("signup.html", errors=errors)

        # If user managed to create a proper account, it will generate a hash for their password
        password_hash = generate_password_hash(password)

        # Here we insert their account details to the database
        user_collection = database_atlas["users"]
        user_collection.insert_one(
            {
                "username": username,
                "password": password_hash,
                "email": email,
                "midi_files": [],
            }
        )

        # This redirects the user to the login page where they must login to access the webpage.
        return redirect(url_for("login"))

    # Renders the signup.html page
    return render_template("signup.html")


# Rendering either the login template if they haven't logged in, otherwise, the home page
@app.route("/login", methods=["GET"])
def login():
    """Renders the login page"""
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("login.html")


# This function is the backend of the login functionality from the login.html file
# @app.route("/login_auth", methods=["POST"])
# def login_auth():
#     """Route for login authentication"""
#     # If a user is already logged in, redirect them to the home page
#     if "user_id" in session:
#         return redirect(url_for("index"))

#     # Else, ask them to login by inputting a username and password
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]
#         session["username"] = username

#         errors = []

#         # Once inputted their username and password, check the database for existing users
#         user = database_atlas.users.find_one({"username": username})

#         # We provide the _id attribute of the user to the user_id in the session
#         if user and check_password_hash(user["password"], password):
#             # User sessions to keep track of who's logged in
#             session["user_id"] = str(user["_id"])
#             return redirect(url_for("index"))

#         # If the username or password does not match we render the login.html template once more
#         errors.append("Invalid username or password!")
#         return render_template("login.html", errors=errors)
#     return None


@app.route("/login_auth", methods=["POST"])
def login_auth():
    """Route for login authentication"""
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        errors = []

        # cleanup()
        user_atlas = database_atlas.users.find_one({"username": username})

        if user_atlas and check_password_hash(user_atlas["password"], password):
            session["user_id"] = str(user_atlas["_id"])

            # clean db before copying from atlas db
            local_user_collection = database["users"]
            local_midi_collection = database["midis"]
            local_user_collection.delete_one({"_id": user_atlas["_id"]})
            local_midi_collection.delete_many({"user_id": str(user_atlas["_id"])})

            # Copy user data
            user_data = user_atlas.copy()
            local_user_collection = database["users"]
            local_user_collection.update_one(
                {"_id": user_atlas["_id"]}, {"$set": user_data}, upsert=True
            )

            # Fetch and copy MIDI data
            midis_atlas = database_atlas["midis"].find(
                {"user_id": str(user_atlas["_id"])}
            )
            local_midi_collection = database["midis"]

            for midi in midis_atlas:
                midi.pop("_id", None)  # Remove '_id' to avoid conflicts
                local_midi_collection.update_one(
                    {"midi_url": midi["midi_url"]}, {"$set": midi}, upsert=True
                )

            return redirect(url_for("index"))

        errors.append("Invalid username or password!")
        return render_template("login.html", errors=errors)

    return None


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Renders the forgot password page"""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        email = request.form["email"]
        errors = []
        user = database_atlas.users.find_one({"email": email, "username": username})

        if not user:
            errors.append("Invalid username or email!")

        if not 8 <= len(password) <= 20:
            errors.append("Password must be between 8 and 20 characters long!")

        if not any(char.isdigit() for char in password):
            errors.append("Password should have at least one number!")

        if not any(char.isalpha() for char in password):
            errors.append("Password should have at least one alphabet!")

        if not confirm_password == password:
            errors.append("Passwords do not match!")

        if errors:
            return render_template("forgot_password.html", errors=errors)
    return None


# Here we have another route, if the user decides to logout,
# it will pop their user_id from the session and redirect them to the login page
@app.route("/logout")
def logout():
    """route for logout"""
    session.pop("user_id", None)
    return redirect(url_for("login"))


# Executing the Flask Application:
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5001, ssl_context="adhoc")
