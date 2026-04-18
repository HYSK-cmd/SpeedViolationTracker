from flask import Flask, jsonify, request, Response
app = Flask(__name__)

@app.get("/get_first_frame")
def first_frame():
    pass

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/livestream")
def livestream():
    pass

def run():
    app.run(host="0.0.0.0", port=5000)