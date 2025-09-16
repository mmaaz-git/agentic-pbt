"""Debug script to understand the should_set_cookie behavior."""

import flask
import flask.sessions

# Exact reproduction of the failing test case
app = flask.Flask(__name__)
app.secret_key = "test-key"

interface = flask.sessions.SecureCookieSessionInterface()
session = flask.sessions.SecureCookieSession()

# The test doesn't modify the session when modified=False
# and doesn't set permanent when permanent=False
print(f"Initial session state:")
print(f"  modified={session.modified}")
print(f"  permanent={session.permanent}")
print(f"  new={session.new}")
print(f"  accessed={session.accessed}")

# Check Flask config
print(f"\nFlask config:")
print(f"  SESSION_REFRESH_EACH_REQUEST={app.config.get('SESSION_REFRESH_EACH_REQUEST')}")

# Call should_set_cookie
result = interface.should_set_cookie(app, session)
print(f"\nshould_set_cookie result: {result}")

# Check what the function actually checks
print(f"\nBreaking down the logic:")
print(f"  session.modified = {session.modified}")
print(f"  session.permanent = {session.permanent}")
print(f"  app.config['SESSION_REFRESH_EACH_REQUEST'] = {app.config.get('SESSION_REFRESH_EACH_REQUEST')}")

# The implementation is:
# return session.modified or (session.permanent and app.config["SESSION_REFRESH_EACH_REQUEST"])
# So with modified=False and permanent=False, it should return False

# Let's check if there's any special initialization
print(f"\nChecking fresh session initialization:")
fresh_session = flask.sessions.SecureCookieSession()
print(f"  Fresh session modified: {fresh_session.modified}")

# What if we check within a request context?
print(f"\nChecking within request context:")
with app.test_request_context():
    ctx_session = flask.sessions.SecureCookieSession()
    ctx_result = interface.should_set_cookie(app, ctx_session)
    print(f"  Result in context: {ctx_result}")
    print(f"  Session state: modified={ctx_session.modified}, permanent={ctx_session.permanent}")