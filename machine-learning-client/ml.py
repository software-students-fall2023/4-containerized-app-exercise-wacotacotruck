from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_data():
    # process request 
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
