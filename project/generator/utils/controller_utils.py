from flask import jsonify


class ControllerUtils:

    @staticmethod
    def error_json_response(error_message):
        return jsonify({"ERROR": error_message})

    @staticmethod
    def json_response(object):
        return jsonify(object)