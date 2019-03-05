from __future__ import print_function
from flask import Flask
from generator.controllers.test_generator_controller import *

import os

app = Flask(__name__)
app.config['UPLOAD_PATH'] = os.path.dirname(os.path.abspath(__file__)) + '/generator/uploads/'
app.register_blueprint(test_generator)
app.debug = True

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
