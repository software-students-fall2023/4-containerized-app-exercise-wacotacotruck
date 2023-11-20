from flask import Flask
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

def call_ml_client(data):
    response = requests.post('http://ml-client:5002/process', json=data)
    return response.json()