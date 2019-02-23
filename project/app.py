from __future__ import print_function
from flask import Flask, render_template, make_response, jsonify, request

app = Flask(__name__)
app.secret_key = 's3cr3t'
app.debug = True


@app.route('/', methods=['GET'])
def index():
    title = 'Create the input'
    return render_template('index.html',
                           title=title)


@app.route('/summarize', methods=['POST'])
def summarize():
    if request.files:
        file = request.files['file-upload'].read()
        text = str(file.decode("utf-8"))
        print(text)
    elif request.form:
        for field_name, value in request.form.items():
            print(field_name)
            print(value)
    return make_response(jsonify({'asd': 'asd'}), 200)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
