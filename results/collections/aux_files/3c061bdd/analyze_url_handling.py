#!/usr/bin/env python3

import inspect
from flask import Flask, Blueprint
from flask.blueprints import BlueprintSetupState

# Check how add_url_rule works with different prefixes
app = Flask(__name__)

# Create test blueprint
bp = Blueprint('test', __name__, url_prefix='/api')

# Check BlueprintSetupState.add_url_rule implementation
print("BlueprintSetupState.add_url_rule source:")
print(inspect.getsource(BlueprintSetupState.add_url_rule))

# Check key property patterns
print("\n\nKey properties to test:")
print("1. URL prefix concatenation logic (lines 98-102)")
print("2. Endpoint naming with name_prefix (line 112)")
print("3. Blueprint name validation (lines 195-199, 427-431)")
print("4. Nested blueprint URL prefix merging (lines 367-374)")
print("5. Subdomain merging for nested blueprints (lines 357-362)")
print("6. Blueprint registration idempotence (lines 306-314)")