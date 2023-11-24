"""Web-app."""
from flask import Flask, url_for, redirect, render_template, make_response, session, request, jsonify, abort
import requests
import os
from flask_session import Session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv 

# Initializes the flask application and loads the .env file to retreive information from the MongoDB Atlas Database
app = Flask(__name__)
load_dotenv()

# This is to monitor Flask's session management. Flask uses a secret key to sign and encrypt session data to prevent tampering and ensure security. 
# This secret key is essential for the proper functioning of user sessions in your Flask application.
# This is essentially when users sign into their account, it simply creates a private session for them (for security and privacy reasons)
sess = Session()
app.secret_key = os.getenv('APP_SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
sess.init_app(app)

# Establish a database connection with the MONGO_URI (MongoDB Atlas connection)
client = MongoClient(os.getenv('MONGO_URI'))

# Checks if the connection has been made, else make an error printout
try:
    client.admin.command('ping')          
    database = client[os.getenv('MONGO_DBNAME')]          
    print('* Connected to MongoDB!')         

except Exception as err:
    print('* "Failed to connect to MongoDB at', os.getenv('MONGO_URI'))
    print('Database connection error:', err) 

# Routes
@app.route("/")
def index():
    """Description of what the function does."""
    return render_template('index.html')

def call_ml_client(data):
    """Description of what the function does."""
    response = requests.post("http://ml-client:5002/process", json=data, timeout=10)
    return response.json()

# This is the function which registers the signup page from the login.html page if the user does click it
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # If there is a user_id in session, it redirects them back to the home page
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    # If there is no account, then we allow the user to creat one. 
    else: 
        if request.method == 'POST':

            # We allow the user to create their username, password, confirm password, email
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            email = request.form['email']

            errors = []
            
            # This checks if there is already a user that has this exact username
            if database.users.find_one({'username': username}):
                errors.append("Username already exists!")
            
            # This checks if there is already a user that has this exact email
            if database.users.find_one({'email': email}):
                errors.append("Email already used, try another or try logging in!")
            
            # This checks if the password is in between 8-20 characters
            if len(password) < 8 & len(password) > 20:
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

            # If there are any errors, it will re-render the signup.html page and allow the user to try again
            if errors:
                return render_template('signup.html', errors=errors)
            
            # If the user managed to create a proper account, it will generate a hash for their password 
            else:
                password_hash = generate_password_hash(password)

            # Here we insert their account details to the database
            collection = database['users']
            collection.insert_one({
                'username': username,
                'password': password_hash,
                'email': email,
                'midi_files': []
            })

            # Once that's done, it will redirect the user to the login page where they must login to access the webpage. 
            return redirect(url_for('login'))
        
        # Renders the signup.html page
        return render_template('signup.html')

# This function is for rendering either the login.html template if they haven't logged in and if they have, then we render the home page
@app.route('/login', methods=['GET'])
def login(): 
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    else:
        return render_template('login.html')

# This function is the backend of the login functionality from the login.html file
@app.route('/login_auth', methods=['POST'])
def login_auth(): 
    # If a user is already logged in, redirect them to the home page
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    # Else, ask them to login by inputting a username and password
    else:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            session['username'] = username

            errors = []

             # Once they've inputted their username and password, we search the database if there is someone already with this username
            user = database.users.find_one({'username': username})

            # If we have a user and the password they gave matches with the hash function, we provide the _id attribute of the user to the user_id in the session
            if user and check_password_hash(user['password'], password):    
                # This is how keep keep track of which user is currently authenticated or logged in. We store the user_id string into the user's session
                session['user_id'] = str(user['_id'])
                return redirect(url_for('index'))
            
            # If the username or password does not match, that means either one is wrong, hence we render the login.html template so they can attempt once more.
            else:
                errors.append("Invalid username or password!")
                return render_template('login.html', errors=errors)
            
@app.route('/forgot_password', methods = ['GET','POST'])
def forgot_password():
    if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            email = request.form['email']

            errors = []
            
            user = database.users.find_one({'email': email, 'username':username})

            if not user:
                errors.append("Invalid username or email!")
            
            if len(password) < 8 & len(password) > 20:
                errors.append("Password must be between 8 and 20 characters long!")
            
            if not any(char.isdigit() for char in password):
                errors.append("Password should have at least one number!")
            
            if not any(char.isalpha() for char in password):
                errors.append("Password should have at least one alphabet!")
            
            if not confirm_password == password:
                errors.append("Passwords do not match!")

            if errors:
                return render_template('forgot_password.html', errors=errors)
            
            else:
                password_hash = generate_password_hash(password)

                filter = {'email': email, 'username':username}
                            
                update = {'$set': {'password': password_hash}}

                database.users.update_one(filter, update)
                                     
                return redirect(url_for('login'))
            
    return render_template('forgot_password.html')

# Here we have another route, if the user decides to logout, it will pop their user_id from the session and redirect them to the login page
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Executing the Flask Application: 
if(__name__ == "__main__"):
    app.run(debug=True)