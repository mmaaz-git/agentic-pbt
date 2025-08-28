import io
import logging
import os
import sys
from unittest import mock

import pytest
from hypothesis import given, strategies as st, settings, assume

import aws_lambda_powertools.package_logger as package_logger
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.logging.logger import set_package_logger


@given(st.one_of(st.none(), st.just(sys.stdout), st.just(sys.stderr)))
def test_idempotence_without_debug(stream):
    """Test that calling set_package_logger_handler multiple times is idempotent when debug is disabled."""
    with mock.patch.dict(os.environ, {constants.POWERTOOLS_DEBUG_ENV: "0"}, clear=True):
        logger = logging.getLogger("aws_lambda_powertools")
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # First call
        package_logger.set_package_logger_handler(stream=stream)
        handlers_after_first = list(logger.handlers)
        propagate_after_first = logger.propagate
        
        # Second call - should be idempotent
        package_logger.set_package_logger_handler(stream=stream)
        handlers_after_second = list(logger.handlers)
        propagate_after_second = logger.propagate
        
        # Check idempotence
        assert len(handlers_after_first) == len(handlers_after_second)
        assert propagate_after_first == propagate_after_second == False
        
        # Check that we have exactly one NullHandler
        assert len(handlers_after_first) == 1
        assert isinstance(handlers_after_first[0], logging.NullHandler)


@given(st.one_of(st.none(), st.just(sys.stdout), st.just(sys.stderr)))
def test_logger_state_invariant_without_debug(stream):
    """Test that logger always has NullHandler and propagate=False when debug is disabled."""
    with mock.patch.dict(os.environ, {constants.POWERTOOLS_DEBUG_ENV: "0"}, clear=True):
        logger = logging.getLogger("aws_lambda_powertools")
        logger.handlers.clear()
        
        package_logger.set_package_logger_handler(stream=stream)
        
        # Invariant: exactly one handler, which is NullHandler
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.NullHandler)
        
        # Invariant: propagate is False
        assert logger.propagate == False


@given(st.sampled_from(["false", "0", "n", "no", "f", "off", "False", "FALSE", "No", "NO"]))
def test_logger_state_with_falsy_debug_values(debug_value):
    """Test logger configuration with various falsy debug values."""
    with mock.patch.dict(os.environ, {constants.POWERTOOLS_DEBUG_ENV: debug_value}, clear=True):
        logger = logging.getLogger("aws_lambda_powertools")
        logger.handlers.clear()
        
        package_logger.set_package_logger_handler()
        
        # Should behave same as disabled
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.NullHandler)
        assert logger.propagate == False


class MockStream(io.StringIO):
    """A mock stream object for testing."""
    def __init__(self):
        super().__init__()
        self.id = id(self)


@given(st.builds(MockStream))
def test_stream_passthrough_with_debug(stream):
    """Test that stream parameter is passed through when debug is enabled."""
    with mock.patch.dict(os.environ, {constants.POWERTOOLS_DEBUG_ENV: "1"}, clear=True):
        with mock.patch('aws_lambda_powertools.logging.logger.set_package_logger') as mock_set_package_logger:
            package_logger.set_package_logger_handler(stream=stream)
            
            # Verify set_package_logger was called with the correct stream
            mock_set_package_logger.assert_called_once_with(stream=stream)


@given(st.sampled_from(["true", "1", "y", "yes", "t", "on", "True", "TRUE", "Yes", "YES"]))
def test_stream_passthrough_with_truthy_debug_values(debug_value):
    """Test that various truthy debug values trigger debug mode."""
    stream = MockStream()
    with mock.patch.dict(os.environ, {constants.POWERTOOLS_DEBUG_ENV: debug_value}, clear=True):
        with mock.patch('aws_lambda_powertools.logging.logger.set_package_logger') as mock_set_package_logger:
            package_logger.set_package_logger_handler(stream=stream)
            
            # Should call set_package_logger when debug is truthy
            mock_set_package_logger.assert_called_once_with(stream=stream)


@given(st.text(min_size=1).filter(lambda x: x.lower() not in ["true", "1", "y", "yes", "t", "on", "false", "0", "n", "no", "f", "off"]))
def test_invalid_debug_values_behavior(debug_value):
    """Test behavior with invalid debug values - should treat as disabled."""
    assume(debug_value.strip())  # Skip empty strings after stripping
    
    with mock.patch.dict(os.environ, {constants.POWERTOOLS_DEBUG_ENV: debug_value}, clear=True):
        logger = logging.getLogger("aws_lambda_powertools")
        logger.handlers.clear()
        
        # Invalid values should be treated as False (no debug)
        package_logger.set_package_logger_handler()
        
        # Should behave like debug disabled
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.NullHandler)
        assert logger.propagate == False


@given(st.integers(min_value=0, max_value=10))
def test_multiple_calls_accumulate_handlers(num_calls):
    """Test that multiple calls to set_package_logger_handler accumulate handlers."""
    with mock.patch.dict(os.environ, {constants.POWERTOOLS_DEBUG_ENV: "0"}, clear=True):
        logger = logging.getLogger("aws_lambda_powertools")
        logger.handlers.clear()
        
        for _ in range(num_calls):
            package_logger.set_package_logger_handler()
        
        # Each call adds a new handler
        if num_calls > 0:
            assert len(logger.handlers) == num_calls
            for handler in logger.handlers:
                assert isinstance(handler, logging.NullHandler)
            assert logger.propagate == False


@given(
    st.lists(
        st.tuples(
            st.booleans(),  # debug enabled/disabled
            st.one_of(st.none(), st.just(sys.stdout), st.just(sys.stderr))  # stream
        ),
        min_size=1,
        max_size=5
    )
)
def test_switching_debug_mode(configs):
    """Test switching between debug and non-debug modes."""
    for debug_enabled, stream in configs:
        debug_value = "1" if debug_enabled else "0"
        
        with mock.patch.dict(os.environ, {constants.POWERTOOLS_DEBUG_ENV: debug_value}, clear=True):
            logger = logging.getLogger("aws_lambda_powertools")
            logger.handlers.clear()
            
            if debug_enabled:
                with mock.patch('aws_lambda_powertools.logging.logger.set_package_logger') as mock_set:
                    package_logger.set_package_logger_handler(stream=stream)
                    mock_set.assert_called_once_with(stream=stream)
            else:
                package_logger.set_package_logger_handler(stream=stream)
                assert len(logger.handlers) == 1
                assert isinstance(logger.handlers[0], logging.NullHandler)
                assert logger.propagate == False