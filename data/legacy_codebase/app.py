import flask
import time

app = flask.Flask(__name__)

@app.route('/')
def index():
    time.sleep(2)
    return "Hello Legacy Flask Code!"