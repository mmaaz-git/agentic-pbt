"""Reproduction script for the permanent flag bug in flask.sessions."""

import flask
import flask.sessions


def test_permanent_flag_modifies_session():
    """Demonstrate that setting session.permanent incorrectly modifies the session."""
    
    print("BUG: Setting session.permanent incorrectly marks session as modified\n")
    print("="*60)
    
    # Create a fresh session
    session = flask.sessions.SecureCookieSession()
    print(f"Fresh session state:")
    print(f"  modified: {session.modified}")
    print(f"  permanent: {session.permanent}")
    print(f"  dict keys: {list(session.keys())}")
    
    # Set permanent to False (its current/default value)
    print(f"\nSetting permanent to False (its current value)...")
    session.permanent = False
    
    print(f"After setting permanent=False:")
    print(f"  modified: {session.modified}")  # BUG: This is now True!
    print(f"  permanent: {session.permanent}")
    print(f"  dict keys: {list(session.keys())}")  # BUG: Now contains '_permanent'!
    
    # This affects should_set_cookie behavior
    print(f"\n" + "="*60)
    print("Impact on should_set_cookie:")
    
    app = flask.Flask(__name__)
    app.secret_key = "test-key"
    interface = flask.sessions.SecureCookieSessionInterface()
    
    # Fresh unmodified session
    clean_session = flask.sessions.SecureCookieSession()
    should_set_clean = interface.should_set_cookie(app, clean_session)
    print(f"  Truly unmodified session: should_set_cookie = {should_set_clean}")
    
    # Session with permanent set to False
    modified_session = flask.sessions.SecureCookieSession()
    modified_session.permanent = False  # This shouldn't modify the session!
    should_set_modified = interface.should_set_cookie(app, modified_session)
    print(f"  After setting permanent=False: should_set_cookie = {should_set_modified}")
    
    print(f"\n" + "="*60)
    print("Why this is a bug:")
    print("1. Setting permanent to its default value shouldn't modify the session")
    print("2. The '_permanent' key is stored in the session dict itself")
    print("3. This causes unnecessary Set-Cookie headers to be sent")
    print("4. It breaks the contract that unmodified sessions don't trigger cookies")
    
    assert clean_session.modified == False, "Clean session should not be modified"
    assert modified_session.modified == True, "BUG: Setting permanent=False modifies session"
    assert '_permanent' in modified_session, "BUG: _permanent stored as session key"
    
    print("\nAll assertions passed - bug confirmed!")


if __name__ == "__main__":
    test_permanent_flag_modifies_session()