"""Web-app."""
from flask import Flask, render_template
import requests

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


def call_ml_client(data):
    """Description of what the function does."""
    response = requests.post("http://localhost:5002/process", json=data, timeout=10)
    return response.json()
