"""Web-app."""
from flask import Flask
import requests

app = Flask(__name__)

@app.route('/')
def index():
    """Description of what the function does."""
    return "Hello, World!"

def call_ml_client(data):
    """Description of what the function does."""
    response = requests.post('http://ml-client:5002/process', json=data, timeout=10)
    return response.json()

# Newline