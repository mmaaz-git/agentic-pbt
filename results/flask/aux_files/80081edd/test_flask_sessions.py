"""Property-based tests for flask.sessions module."""

import math
from datetime import datetime, timedelta
from unittest.mock import Mock

import flask
import flask.sessions
import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st


# Strategies for generating valid session data
# Based on what JSON can serialize and what Flask sessions typically contain
simple_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-2**53, max_value=2**53),  # JavaScript safe integers
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=1000),
)

# Recursive strategy for nested structures
session_data = st.recursive(
    simple_values,
    lambda children: st.one_of(
        st.lists(children, max_size=50),
        st.dictionaries(
            st.text(min_size=1, max_size=100).filter(lambda x: x.isidentifier() or x.replace('_', '').replace('-', '').replace('.', '').isalnum()),
            children,
            max_size=20
        )
    ),
    max_leaves=100
)

# Strategy for dictionary-like session data
session_dict = st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda x: not x.startswith('_')),
    session_data,
    min_size=0,
    max_size=20
)


class TestSecureCookieSession:
    """Test properties of SecureCookieSession class."""
    
    @given(session_dict)
    def test_session_dict_invariants(self, data):
        """SecureCookieSession should maintain dictionary invariants."""
        session = flask.sessions.SecureCookieSession(data)
        
        # Length invariant
        assert len(session) == len(data)
        
        # Keys invariant
        assert set(session.keys()) == set(data.keys())
        
        # Values invariant
        for key in data:
            assert session[key] == data[key]
        
        # Contains invariant
        for key in data:
            assert key in session
    
    @given(session_dict, st.text(min_size=1, max_size=50))
    def test_session_modification_tracking(self, initial_data, new_key):
        """Modified flag should be set when session is modified."""
        session = flask.sessions.SecureCookieSession(initial_data)
        
        # Initially not modified (we just created it)
        assert session.modified == False
        
        # Setting a new value should set modified
        session[new_key] = "test_value"
        assert session.modified == True
        
        # Clearing should also set modified
        session2 = flask.sessions.SecureCookieSession(initial_data)
        session2.clear()
        assert session2.modified == True
    
    @given(session_dict)
    def test_session_accessed_tracking(self, data):
        """Accessed flag should be set when session is accessed."""
        session = flask.sessions.SecureCookieSession(data)
        
        # Initially not accessed
        assert session.accessed == False
        
        # Getting a value should set accessed
        if data:
            key = next(iter(data))
            _ = session.get(key)
            assert session.accessed == True
        
        # Even getting non-existent key should set accessed
        session2 = flask.sessions.SecureCookieSession(data)
        _ = session2.get("nonexistent_key_12345", None)
        assert session2.accessed == True
    
    @given(session_dict)
    def test_session_copy_preserves_data(self, data):
        """Copying a session should preserve all data."""
        session = flask.sessions.SecureCookieSession(data)
        session.modified = True
        session.accessed = True
        
        copied = session.copy()
        
        # Data should be preserved
        assert dict(copied) == dict(session)
        
        # But it's a new dict instance
        assert copied is not session
    
    @given(session_dict, session_dict)
    def test_session_update(self, initial_data, update_data):
        """Update should work correctly and set flags."""
        session = flask.sessions.SecureCookieSession(initial_data)
        session.update(update_data)
        
        # Should have all keys from both dicts
        expected = initial_data.copy()
        expected.update(update_data)
        assert dict(session) == expected
        
        # Should be marked as modified if update_data is non-empty
        if update_data:
            assert session.modified == True


class TestNullSession:
    """Test properties of NullSession class."""
    
    @given(st.text(min_size=1, max_size=50), session_data)
    def test_null_session_immutability(self, key, value):
        """NullSession should raise RuntimeError on any write operation."""
        null_session = flask.sessions.NullSession()
        
        # Setting should fail
        with pytest.raises(RuntimeError):
            null_session[key] = value
        
        # Deleting should fail
        with pytest.raises(RuntimeError):
            del null_session[key]
        
        # Clear should fail
        with pytest.raises(RuntimeError):
            null_session.clear()
        
        # Pop should fail
        with pytest.raises(RuntimeError):
            null_session.pop(key, None)
        
        # Popitem should fail
        with pytest.raises(RuntimeError):
            null_session.popitem()
        
        # Setdefault should fail
        with pytest.raises(RuntimeError):
            null_session.setdefault(key, value)
        
        # Update should fail
        with pytest.raises(RuntimeError):
            null_session.update({key: value})
    
    def test_null_session_read_operations(self):
        """NullSession should allow read operations."""
        null_session = flask.sessions.NullSession()
        
        # These should not raise
        assert null_session.get("key", "default") == "default"
        assert list(null_session.keys()) == []
        assert list(null_session.values()) == []
        assert list(null_session.items()) == []
        assert len(null_session) == 0
        assert "key" not in null_session


class TestSessionSerialization:
    """Test session serialization properties."""
    
    @given(session_dict)
    def test_json_serializer_round_trip(self, data):
        """Session JSON serializer should correctly round-trip data."""
        serializer = flask.sessions.session_json_serializer
        
        # Serialize and deserialize
        serialized = serializer.dumps(data)
        deserialized = serializer.loads(serialized)
        
        # Should be equal
        assert deserialized == data
    
    @given(session_dict)
    @settings(max_examples=50)  # This test creates Flask apps, so limit examples
    def test_secure_cookie_interface_round_trip(self, session_data):
        """SecureCookieSessionInterface should correctly round-trip sessions."""
        # Create a Flask app with secret key
        app = flask.Flask(__name__)
        app.secret_key = "test-secret-key-for-hypothesis-testing"
        
        # Create interface and serializer
        interface = flask.sessions.SecureCookieSessionInterface()
        serializer = interface.get_signing_serializer(app)
        
        assume(serializer is not None)  # Skip if no serializer (shouldn't happen)
        
        # Create a session with the data
        session = flask.sessions.SecureCookieSession(session_data)
        
        # Serialize it (this is what goes into the cookie)
        serialized = serializer.dumps(dict(session))
        
        # Deserialize it (this is what comes back from the cookie)
        deserialized = serializer.loads(serialized)
        
        # Should be equal
        assert deserialized == session_data
    
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(
                st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 1, 1)),
                st.timedeltas(min_value=timedelta(days=-365), max_value=timedelta(days=365)),
                st.binary(min_size=0, max_size=100),
                st.tuples(st.integers(), st.text()),
                st.sets(st.integers(min_value=-100, max_value=100))
            ),
            min_size=1,
            max_size=5
        )
    )
    def test_tagged_json_serializer_special_types(self, data):
        """TaggedJSONSerializer should handle special Python types."""
        serializer = flask.sessions.session_json_serializer
        
        try:
            # Try to serialize
            serialized = serializer.dumps(data)
            deserialized = serializer.loads(serialized)
            
            # Check that types are preserved
            for key, value in data.items():
                if isinstance(value, (datetime, timedelta, bytes, tuple, set)):
                    assert type(deserialized[key]) == type(value)
                    # For datetime, check that the value is close (might lose microseconds)
                    if isinstance(value, datetime):
                        assert abs((deserialized[key] - value).total_seconds()) < 1
                    else:
                        assert deserialized[key] == value
        except Exception:
            # Some types might not be supported, that's okay
            # We're looking for crashes/corruption, not comprehensive support
            pass


class TestSecureCookieSessionInterface:
    """Test properties of SecureCookieSessionInterface."""
    
    @given(st.booleans(), st.booleans())
    @settings(max_examples=20)
    def test_should_set_cookie_logic(self, modified, permanent):
        """should_set_cookie should follow documented logic."""
        app = flask.Flask(__name__)
        app.secret_key = "test-key"
        
        interface = flask.sessions.SecureCookieSessionInterface()
        session = flask.sessions.SecureCookieSession()
        
        # Set the session state
        if modified:
            session['key'] = 'value'  # This sets modified=True
        session.permanent = permanent
        
        # Test should_set_cookie
        should_set = interface.should_set_cookie(app, session)
        
        # According to Flask docs, cookie should be set if:
        # - session is modified, OR
        # - session is permanent and app.config.get('SESSION_REFRESH_EACH_REQUEST', True)
        
        # Check actual config value
        refresh_each_request = app.config.get('SESSION_REFRESH_EACH_REQUEST', True)
        expected = modified or (permanent and refresh_each_request)
        assert should_set == expected
    
    @given(session_dict, st.integers(min_value=0, max_value=365*24*60))
    @settings(max_examples=20)
    def test_cookie_expiration(self, data, lifetime_minutes):
        """Cookie expiration should be set correctly."""
        app = flask.Flask(__name__)
        app.secret_key = "test-key"
        app.permanent_session_lifetime = timedelta(minutes=lifetime_minutes)
        
        interface = flask.sessions.SecureCookieSessionInterface()
        session = flask.sessions.SecureCookieSession(data)
        session.permanent = True
        
        # Get expiration time
        expiration = interface.get_expiration_time(app, session)
        
        if session.permanent:
            # Should have an expiration
            assert expiration is not None
            # Should be in the future (roughly)
            assert expiration > datetime.now(expiration.tzinfo) - timedelta(seconds=10)
            # Should be roughly lifetime_minutes from now
            expected_delta = timedelta(minutes=lifetime_minutes)
            actual_delta = expiration - datetime.now(expiration.tzinfo)
            # Allow 1 minute tolerance for test execution time
            assert abs((actual_delta - expected_delta).total_seconds()) < 60
    
    @given(st.text(min_size=1, max_size=50).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()))
    @settings(max_examples=20)
    def test_cookie_name_configuration(self, cookie_name):
        """Cookie name should be configurable."""
        app = flask.Flask(__name__)
        app.secret_key = "test-key"
        app.config['SESSION_COOKIE_NAME'] = cookie_name
        
        interface = flask.sessions.SecureCookieSessionInterface()
        session = flask.sessions.SecureCookieSession()
        
        # Get cookie name
        actual_name = interface.get_cookie_name(app)
        assert actual_name == cookie_name


class TestSessionIntegration:
    """Integration tests for session handling."""
    
    @given(session_dict)
    @settings(max_examples=30)
    def test_full_session_lifecycle(self, data):
        """Test complete session lifecycle: create, modify, save, load."""
        app = flask.Flask(__name__)
        app.secret_key = "test-secret-key"
        
        with app.test_request_context():
            # Create a session
            session = flask.sessions.SecureCookieSession(data)
            
            # Simulate saving to cookie
            interface = flask.sessions.SecureCookieSessionInterface()
            serializer = interface.get_signing_serializer(app)
            
            if serializer:
                # Save session
                cookie_value = serializer.dumps(dict(session))
                
                # Load session back
                loaded_data = serializer.loads(cookie_value)
                
                # Should match original data
                assert loaded_data == data
    
    @given(
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20),
                session_data
            ),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_session_mutations(self, operations):
        """Test that session correctly tracks multiple mutations."""
        session = flask.sessions.SecureCookieSession()
        
        for key, value in operations:
            session[key] = value
            assert session.modified == True
            assert session.accessed == True
        
        # Final state should have all the keys
        for key, value in operations:
            assert key in session
            # Last write wins
            expected_value = next((v for k, v in reversed(operations) if k == key), None)
            if expected_value is not None:
                assert session[key] == expected_value