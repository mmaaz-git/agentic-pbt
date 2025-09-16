#!/usr/bin/env python3
import flask.json
import json

# Reproduce the bug
data = {'b': 1, 'a': 2, '0': 3, '/': 4}

# Using flask.json.dumps without app context
flask_encoded = flask.json.dumps(data)
flask_decoded = flask.json.loads(flask_encoded)

print("Bug reproduction:")
print(f"Original dict: {data}")
print(f"After flask.json.dumps/loads: {flask_decoded}")
print(f"Keys preserved order: {list(flask_decoded.keys())}")
print(f"Expected sorted keys: {sorted(data.keys())}")
print(f"BUG: Keys are NOT sorted as expected!")
print()

# Show that with app context it works correctly
from flask import Flask
app = Flask(__name__)

with app.app_context():
    flask_encoded_with_context = flask.json.dumps(data)
    flask_decoded_with_context = flask.json.loads(flask_encoded_with_context)
    print("With Flask app context:")
    print(f"Keys after dumps/loads: {list(flask_decoded_with_context.keys())}")
    print(f"Keys ARE sorted correctly: {list(flask_decoded_with_context.keys()) == sorted(data.keys())}")