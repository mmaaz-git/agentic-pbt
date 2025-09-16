"""Minimal test to reproduce the should_set_cookie issue."""

import flask
import flask.sessions


def test_should_set_cookie_minimal():
    """Minimal reproduction of the failing test."""
    # Exact parameters from the failing test
    modified = False
    permanent = False
    
    app = flask.Flask(__name__)
    app.secret_key = "test-key"
    
    interface = flask.sessions.SecureCookieSessionInterface()
    session = flask.sessions.SecureCookieSession()
    
    print(f"Before any operations:")
    print(f"  session.modified = {session.modified}")
    print(f"  session.permanent = {session.permanent}")
    print(f"  session.accessed = {session.accessed}")
    
    # Set the session state (from the test)
    if modified:
        session['key'] = 'value'  # This sets modified=True
    session.permanent = permanent
    
    print(f"\nAfter setting state:")
    print(f"  session.modified = {session.modified}")
    print(f"  session.permanent = {session.permanent}")
    print(f"  session.accessed = {session.accessed}")
    
    # Test should_set_cookie
    should_set = interface.should_set_cookie(app, session)
    
    print(f"\nshould_set_cookie returned: {should_set}")
    
    # Check actual config value
    refresh_each_request = app.config.get('SESSION_REFRESH_EACH_REQUEST', True)
    expected = modified or (permanent and refresh_each_request)
    
    print(f"\nExpected: {expected}")
    print(f"Got: {should_set}")
    print(f"Test passes: {should_set == expected}")
    
    assert should_set == expected


if __name__ == "__main__":
    test_should_set_cookie_minimal()