# app/utils/helpers.py
from flask import jsonify

def error_response(message, status_code):
    return jsonify({"error": message}), status_code

def success_response(data, status_code=200):
    return jsonify(data), status_code

# You could add more helpers here if needed