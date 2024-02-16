import os

import matplotlib.pyplot as plt
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return os.getcwd()

@app.route('exec_runtime')
def exec_runtime():
    requests.get('')
    return ''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)