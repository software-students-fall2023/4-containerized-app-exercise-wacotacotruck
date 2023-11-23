"""Web-app."""
from flask import Flask, url_for, redirect, render_template, make_response, session, request,  jsonify, abort
import requests
import os

app = Flask(__name__)


@app.route("/")
def index():
    """Description of what the function does."""
    return "Hello, World!"


def call_ml_client(data):
    """Description of what the function does."""
    response = requests.post("http://ml-client:5002/process", json=data, timeout=10)
    return response.json()
