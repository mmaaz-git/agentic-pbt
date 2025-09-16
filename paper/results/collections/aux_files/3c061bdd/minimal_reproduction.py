#!/usr/bin/env python3

from flask import Flask, Blueprint

# Minimal reproduction of the bug
app = Flask(__name__)
bp = Blueprint('test', __name__)  # No url_prefix

# This fails with ValueError
bp.add_url_rule("", endpoint="root", view_func=lambda: "root")
app.register_blueprint(bp)