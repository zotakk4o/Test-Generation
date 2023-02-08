from __future__ import print_function
from flask import Flask
from project.generator.controllers.test_generator_controller import *

import os

app = Flask(__name__)
app.config['UPLOAD_PATH'] = os.path.dirname(os.path.abspath(__file__)) + f"{os.sep}generator{os.sep}uploads{os.sep}"
app.register_blueprint(test_generator)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
