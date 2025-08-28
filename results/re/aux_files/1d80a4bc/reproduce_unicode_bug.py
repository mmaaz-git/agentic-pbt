import flask
import flask.ctx
import sys

# Create a Flask app
app = flask.Flask('test_app')

# Create a WSGI environment with Unicode character in PATH_INFO
environ = {
    'REQUEST_METHOD': 'GET',
    'PATH_INFO': '/Ā',  # Latin Extended-A character (U+0100)
    'SERVER_NAME': 'localhost',
    'SERVER_PORT': '80',
    'wsgi.version': (1, 0),
    'wsgi.url_scheme': 'http',
    'wsgi.input': None,
    'wsgi.errors': sys.stderr,
    'wsgi.multithread': False,
    'wsgi.multiprocess': False,
    'wsgi.run_once': False,
}

print("Attempting to create RequestContext with Unicode PATH_INFO='/Ā'")
try:
    ctx = flask.ctx.RequestContext(app, environ)
    print("Success! RequestContext created.")
    ctx.push()
    print("Context pushed successfully.")
    ctx.pop()
    print("Context popped successfully.")
except UnicodeEncodeError as e:
    print(f"UnicodeEncodeError: {e}")
    print("\nThis error occurs because Werkzeug's _wsgi_decoding_dance function")
    print("tries to encode the PATH_INFO with 'latin-1' codec, which cannot")
    print("handle characters outside the Latin-1 range (U+0000 to U+00FF).")
except Exception as e:
    print(f"Unexpected error: {e}")