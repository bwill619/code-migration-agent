import flask
import time

app = flask.Flask(__name__)

@app.route('/', methods=["GET"])
def index():
    time.sleep(2)
    return "Hello Legacy Flask Code!"

@app.route("/process", methods=["GET"])
def process_data():
    time.sleep(2)
    return "Data Processed Successfully"