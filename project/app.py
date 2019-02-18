from __future__ import print_function
from flask import Flask, render_template, make_response

app = Flask(__name__)
app.secret_key = 's3cr3t'
app.debug = True

@app.route('/', methods=['GET'])
def index():
    title = 'Create the input'
    return render_template('index.html',
                           title=title)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)