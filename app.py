from flask import Flask, request, render_template, jsonify

app = Flask(__file__)

@app.route("/", method=["GET", "POST"])
def home():
    if request.method == "POST":
        # return render_template("")
        pass
    pass
