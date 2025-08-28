import logging
from unittest.mock import Mock
from hypothesis import given, strategies as st, assume
import flask.logging


@given(
    logger_level=st.sampled_from([0, logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]),
    handler_level=st.sampled_from([0, logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]),
    propagate=st.booleans(),
    has_parent=st.booleans(),
    parent_has_handler=st.booleans()
)
def test_has_level_handler_with_direct_handler(logger_level, handler_level, propagate, has_parent, parent_has_handler):
    """Test that has_level_handler correctly detects handlers at or below effective level"""
    # Create a fresh logger with unique name to avoid state pollution
    import uuid
    logger_name = f"test_{uuid.uuid4()}"
    logger = logging.getLogger(logger_name)
    
    # Clear any existing handlers
    logger.handlers.clear()
    logger.propagate = propagate
    
    if logger_level > 0:
        logger.setLevel(logger_level)
    
    # Add a handler at the specified level
    handler = logging.StreamHandler()
    handler.setLevel(handler_level)
    logger.addHandler(handler)
    
    effective_level = logger.getEffectiveLevel()
    
    # has_level_handler should return True if handler.level <= effective_level
    result = flask.logging.has_level_handler(logger)
    expected = handler_level <= effective_level
    
    assert result == expected, f"has_level_handler returned {result}, expected {expected} for handler_level={handler_level}, effective_level={effective_level}"


@given(
    child_level=st.sampled_from([0, logging.DEBUG, logging.INFO, logging.WARNING]),
    parent_handler_level=st.sampled_from([0, logging.DEBUG, logging.INFO, logging.WARNING]),
    child_propagate=st.booleans()
)
def test_has_level_handler_hierarchy_traversal(child_level, parent_handler_level, child_propagate):
    """Test that has_level_handler correctly traverses the logger hierarchy"""
    import uuid
    
    # Create parent logger with handler
    parent_name = f"parent_{uuid.uuid4()}"
    parent = logging.getLogger(parent_name)
    parent.handlers.clear()
    
    parent_handler = logging.StreamHandler()
    parent_handler.setLevel(parent_handler_level)
    parent.addHandler(parent_handler)
    
    # Create child logger
    child_name = f"{parent_name}.child"
    child = logging.getLogger(child_name)
    child.handlers.clear()
    child.propagate = child_propagate
    
    if child_level > 0:
        child.setLevel(child_level)
    
    effective_level = child.getEffectiveLevel()
    result = flask.logging.has_level_handler(child)
    
    # If propagate is False, should only check child's handlers (none)
    # If propagate is True, should check parent's handler
    if child_propagate:
        expected = parent_handler_level <= effective_level
    else:
        expected = False  # Child has no handlers and doesn't propagate
    
    assert result == expected, f"has_level_handler returned {result}, expected {expected} for propagate={child_propagate}, parent_handler_level={parent_handler_level}, effective_level={effective_level}"


@given(
    debug=st.booleans(),
    initial_level=st.sampled_from([0, logging.DEBUG, logging.INFO]),
    app_name=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_create_logger_debug_mode(debug, initial_level, app_name):
    """Test that create_logger sets DEBUG level when app.debug is True and logger has no level"""
    import uuid
    
    # Create a unique logger name to avoid conflicts
    logger_name = f"app_{uuid.uuid4()}_{app_name}"
    
    # Mock Flask app
    app = Mock()
    app.debug = debug
    app.name = logger_name
    
    # Pre-create the logger with initial level
    test_logger = logging.getLogger(logger_name)
    test_logger.handlers.clear()
    test_logger.setLevel(initial_level)
    
    # Call create_logger
    result_logger = flask.logging.create_logger(app)
    
    # Verify the logger name matches
    assert result_logger.name == logger_name
    
    # Check debug level setting behavior
    if debug and initial_level == 0:
        # Should set to DEBUG when app.debug is True and logger has no level (0)
        assert result_logger.level == logging.DEBUG, f"Logger level should be DEBUG when app.debug=True and initial level was 0, got {result_logger.level}"
    else:
        # Should preserve the initial level
        assert result_logger.level == initial_level, f"Logger level should remain {initial_level}, got {result_logger.level}"


@given(
    app_name=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    has_existing_handler=st.booleans()
)
def test_create_logger_handler_addition(app_name, has_existing_handler):
    """Test that create_logger adds default handler when no level handler exists"""
    import uuid
    
    logger_name = f"handler_test_{uuid.uuid4()}_{app_name}"
    
    # Mock Flask app
    app = Mock()
    app.debug = False
    app.name = logger_name
    
    # Pre-create logger
    test_logger = logging.getLogger(logger_name)
    test_logger.handlers.clear()
    
    if has_existing_handler:
        # Add a handler that will handle the effective level
        handler = logging.StreamHandler()
        handler.setLevel(0)  # Will handle everything
        test_logger.addHandler(handler)
    
    initial_handler_count = len(test_logger.handlers)
    
    # Call create_logger
    result_logger = flask.logging.create_logger(app)
    
    final_handler_count = len(result_logger.handlers)
    
    if has_existing_handler:
        # Should not add another handler
        assert final_handler_count == initial_handler_count
    else:
        # Should add the default handler
        assert final_handler_count == initial_handler_count + 1
        # Check that it's the default handler
        assert flask.logging.default_handler in result_logger.handlers