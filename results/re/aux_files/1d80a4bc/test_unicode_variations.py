import flask
import flask.ctx
import sys

app = flask.Flask('test_app')

test_cases = [
    ('/hello', 'ASCII - should work'),
    ('/café', 'Latin-1 (U+00E9) - should work'),  
    ('/Ā', 'Latin Extended-A (U+0100) - will fail'),
    ('/你好', 'Chinese characters - will fail'),
    ('/🦄', 'Emoji - will fail'),
    ('/путь', 'Cyrillic - will fail'),
]

for path, description in test_cases:
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': path,
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
    
    try:
        ctx = flask.ctx.RequestContext(app, environ)
        ctx.push()
        ctx.pop()
        print(f"✓ {description}: '{path}'")
    except UnicodeEncodeError:
        print(f"✗ {description}: '{path}' - UnicodeEncodeError")
    except Exception as e:
        print(f"? {description}: '{path}' - {type(e).__name__}: {e}")