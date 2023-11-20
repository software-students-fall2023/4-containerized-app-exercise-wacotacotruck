"""Module for the machine learning client."""
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/process", methods=["POST"])
def process_data():
    """Description of what the function does."""
    result = {}
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
