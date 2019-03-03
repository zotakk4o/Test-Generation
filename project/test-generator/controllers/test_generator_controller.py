from flask import render_template, make_response, request, Blueprint
from flask import current_app as app
from utils.controller_utils import ControllerUtils
from utils.file_utils import FileUtils
from nltk import sent_tokenize
from constants.test_generator_controller_constants import *
from test_generator import TestGenerator

import os

test_generator = Blueprint('simple_page', __name__,
                           template_folder='templates')


@test_generator.route('/', methods=['GET'])
def index():
    return render_template('index.html',
                           gaps_name=GAP_INPUT_NAME,
                           completion_name=COMPLETION_INPUT_NAME,
                           test_size_name=TEST_SIZE_INPUT_NAME,
                           raw_text_name=RAW_TEXT_NAME,
                           file_upload_name=FILE_UPLOAD_NAME)


@test_generator.route('/generate-test', methods=['POST'])
def generate_test():
    text = ""
    answer = {
        "GAPS": [],
        "COMPLETION": [],
        "BONUSES": []
    }
    file_handler = {
        'pdf': FileUtils.get_pdf_text,
        'docx': FileUtils.get_docx_text,
        'default': FileUtils.read_file
    }
    if request.files:
        file = request.files[FILE_UPLOAD_NAME]
        file_name, file_extension = FileUtils.get_file_config(file)
        file_path = os.path.join(app.config['UPLOAD_PATH'], file_name)

        if file_extension in ALLOWED_EXTENSIONS:
            file.save(file_path)
            if file_extension in file_handler.keys():
                text = file_handler[file_extension](file_path)
            else:
                text = file_handler['default'](file_path)
            os.remove(file_path)
    elif RAW_TEXT_NAME in request.form.keys():
        text = request.form[RAW_TEXT_NAME]

    if len(sent_tokenize(text)) < MINIMUM_SENTENCES:
        return make_response(ControllerUtils.error_json_response(TEXT_LENGTH_ERROR), 400)

    test_generator_object = TestGenerator(text, int(request.form[TEST_SIZE_INPUT_NAME]))

    is_gap = GAP_INPUT_NAME in request.form.keys()
    is_completion = COMPLETION_INPUT_NAME in request.form.keys()

    if is_gap:
        answer["GAPS"] = test_generator_object.extract_gaps(not is_completion)

    if is_completion:
        answer["COMPLETION"] = test_generator_object.extract_sentence_completion(not is_gap)

    answer["BONUSES"] = test_generator_object.extract_bonuses()

    return make_response(ControllerUtils.json_response(answer), 200)
