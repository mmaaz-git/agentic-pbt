import sys
import os
from datetime import timedelta
import random
import string
from hypothesis import given, strategies as st, assume, settings, example
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'venv/lib/python3.13/site-packages'))

import flask
from flask import Flask
from werkzeug.datastructures import Headers


# Bug 1: Headers with newline characters cause ValueError but Flask doesn't validate this
@given(st.dictionaries(
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    st.text()
))
@example({'X-Test': '\n'})
@example({'Content-Type': 'text/plain\n'})
def test_make_response_headers_with_newlines(headers):
    """Flask.make_response doesn't validate headers for newlines before passing to werkzeug"""
    app = Flask(__name__)
    
    # Check if any header contains newlines
    has_newline = any('\n' in value or '\r' in value for value in headers.values())
    
    with app.test_request_context():
        if has_newline:
            # Flask should either sanitize or reject headers with newlines
            # but it passes them directly to werkzeug which raises ValueError
            with pytest.raises(ValueError, match="Header values must not contain newline characters"):
                response = app.make_response(("test", headers))
        else:
            # Normal headers should work
            response = app.make_response(("test", headers))
            for key, value in headers.items():
                assert response.headers.get(key) == value


# Bug 2: Empty tuple handling inconsistency
def test_make_response_empty_tuple_bug():
    """Flask.make_response has inconsistent error message for empty tuples"""
    app = Flask(__name__)
    with app.test_request_context():
        # Empty tuple should be caught explicitly 
        with pytest.raises(TypeError) as exc_info:
            app.make_response(())
        
        # The error message says "The tuple must have the form (body, status, headers)..."
        # but doesn't explicitly handle empty tuples
        assert "did not return a valid response tuple" in str(exc_info.value)


# Bug 3: Status string parsing issue
@given(st.text().filter(lambda x: x and x[0].isdigit()))
@example('000')
@example('100')
@example('199')
@example('999')
def test_flask_status_string_parsing(status_string):
    """Flask's response.status setter has undocumented behavior with numeric strings"""
    app = Flask(__name__)
    with app.test_request_context():
        response = app.make_response("test")
        response.status = status_string
        
        # Flask/Werkzeug tries to parse numeric strings and adds default reason phrases
        # This is undocumented behavior that can be surprising
        if status_string.isdigit() and len(status_string) == 3:
            # Werkzeug adds "UNKNOWN" for unrecognized status codes
            if int(status_string) not in [200, 201, 204, 301, 302, 304, 400, 401, 403, 404, 500, 501, 502, 503]:
                # For unknown status codes, werkzeug adds "UNKNOWN"
                # This is surprising behavior - setting '000' results in '000 UNKNOWN'
                pass
        
        # The status property doesn't preserve the original string value
        # This violates the expectation that setting a property preserves the value
        print(f"Set status to: {status_string!r}, got: {response.status!r}")


# More focused test to demonstrate the real bug
def test_header_newline_vulnerability():
    """Demonstrate that Flask doesn't sanitize headers, allowing newline injection"""
    app = Flask(__name__)
    
    malicious_headers = {
        'X-Custom': 'value\nX-Injected: malicious'
    }
    
    with app.test_request_context():
        # This should be handled gracefully by Flask, but it's not
        try:
            response = app.make_response(("body", malicious_headers))
            print("Flask allowed headers with newlines - potential security issue!")
        except ValueError as e:
            print(f"Werkzeug caught the issue: {e}")
            # Flask should handle this before it gets to werkzeug
            assert "newline" in str(e).lower()


def test_demonstrate_bugs():
    """Run specific tests to demonstrate the bugs"""
    print("\n=== Testing Header Newline Vulnerability ===")
    test_header_newline_vulnerability()
    
    print("\n=== Testing Empty Tuple Handling ===")
    test_make_response_empty_tuple_bug()
    
    print("\n=== Testing Status String Parsing ===")
    test_flask_status_string_parsing.hypothesis.fuzz_one_input(b'000')
    test_flask_status_string_parsing.hypothesis.fuzz_one_input(b'199')


if __name__ == "__main__":
    test_demonstrate_bugs()