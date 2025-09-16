"""
Property-based tests for aws_lambda_powertools.logging module.
Testing fundamental properties that the code claims to have.
"""

import logging
import os
import sys
from unittest.mock import patch, MagicMock
import json
import random
import string

from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the module to path
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.logging.filters import SuppressFilter
from aws_lambda_powertools.logging.exceptions import InvalidLoggerSamplingRateError


# Strategy for valid sampling rates (0.0 to 1.0)
valid_sampling_rates = st.floats(min_value=0.0, max_value=1.0)

# Strategy for invalid sampling rates (non-numeric strings)
invalid_sampling_rates = st.text(min_size=1).filter(lambda x: not x.replace('.', '', 1).replace('-', '', 1).isdigit())

# Strategy for log levels
log_levels = st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
log_level_ints = st.sampled_from([logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL])

# Strategy for service names
service_names = st.text(min_size=1, max_size=50, alphabet=string.ascii_letters + string.digits + '_-')

# Strategy for logger names
logger_names = st.text(min_size=1, max_size=30, alphabet=string.ascii_letters + string.digits + '_')


class TestSamplingRateProperties:
    """Test properties related to sampling rate validation and behavior."""
    
    @given(rate=valid_sampling_rates)
    @settings(max_examples=100)
    def test_valid_sampling_rate_acceptance(self, rate):
        """Property: Valid sampling rates (0.0 to 1.0) should be accepted without error."""
        # The Logger should accept any float between 0.0 and 1.0
        logger = Logger(service="test", sampling_rate=rate)
        assert logger.sampling_rate == rate
    
    @given(rate=invalid_sampling_rates)
    @settings(max_examples=50)
    def test_invalid_sampling_rate_rejection(self, rate):
        """Property: Invalid sampling rates (non-numeric strings) should raise InvalidLoggerSamplingRateError."""
        # Test that invalid rates are properly rejected during _configure_sampling
        with patch('random.random', return_value=0.5):
            logger = Logger(service="test", sampling_rate=rate)
            # The error should be raised when _configure_sampling is called
            with pytest.raises(InvalidLoggerSamplingRateError) as exc_info:
                logger._configure_sampling()
            assert "Expected a float value ranging 0 to 1" in str(exc_info.value)
    
    @given(rate=st.floats(min_value=0.0, max_value=1.0, exclude_min=False, exclude_max=False))
    @settings(max_examples=100)
    def test_sampling_rate_debug_level_property(self, rate):
        """Property: When random.random() <= sampling_rate, log level should be set to DEBUG."""
        # Generate multiple random values to test the sampling logic
        for _ in range(10):
            random_value = random.random()
            with patch('random.random', return_value=random_value):
                logger = Logger(service="test", sampling_rate=rate, level="INFO")
                
                # Based on the code logic: if random.random() <= float(self.sampling_rate)
                if random_value <= rate:
                    assert logger.log_level == logging.DEBUG
                else:
                    assert logger.log_level == logging.INFO


class TestSuppressFilterProperties:
    """Test properties related to SuppressFilter behavior."""
    
    @given(
        logger_name=logger_names,
        record_name=logger_names
    )
    def test_suppress_filter_containment_property(self, logger_name, record_name):
        """Property: SuppressFilter should reject records where logger_name is in record_name."""
        filter_obj = SuppressFilter(logger_name)
        
        # Create a mock log record
        record = MagicMock(spec=logging.LogRecord)
        record.name = record_name
        
        # The filter returns False (rejects) if logger_name is in record_name
        result = filter_obj.filter(record)
        
        # Based on the code: return self.logger not in logger
        expected = logger_name not in record_name
        assert result == expected
    
    @given(
        parent_logger=st.text(min_size=1, max_size=20, alphabet=string.ascii_lowercase),
        child_suffix=st.text(min_size=1, max_size=20, alphabet=string.ascii_lowercase)
    )
    def test_suppress_filter_child_logger_property(self, parent_logger, child_suffix):
        """Property: Child loggers (parent.child) should be suppressed by parent filter."""
        filter_obj = SuppressFilter(parent_logger)
        
        # Child logger name includes parent
        child_logger_name = f"{parent_logger}.{child_suffix}"
        
        record = MagicMock(spec=logging.LogRecord)
        record.name = child_logger_name
        
        # Should return False (suppress) because parent_logger is in child_logger_name
        result = filter_obj.filter(record)
        assert result == False


class TestKeyManagementProperties:
    """Test properties related to key management in Logger."""
    
    @given(
        keys=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet=string.ascii_letters),
            values=st.text(min_size=0, max_size=50),
            min_size=1,
            max_size=10
        )
    )
    def test_append_and_get_keys_property(self, keys):
        """Property: Keys appended should be retrievable via get_current_keys."""
        logger = Logger(service="test")
        
        # Append keys
        logger.append_keys(**keys)
        
        # Get current keys
        current_keys = logger.get_current_keys()
        
        # All appended keys should be in current keys
        for key, value in keys.items():
            assert key in current_keys
            assert current_keys[key] == value
    
    @given(
        initial_keys=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet=string.ascii_letters),
            values=st.text(min_size=0, max_size=50),
            min_size=1,
            max_size=5
        ),
        keys_to_remove=st.lists(
            st.text(min_size=1, max_size=20, alphabet=string.ascii_letters),
            min_size=1,
            max_size=3
        )
    )
    def test_remove_keys_property(self, initial_keys, keys_to_remove):
        """Property: Keys removed should not be in current keys."""
        logger = Logger(service="test")
        
        # Append initial keys
        logger.append_keys(**initial_keys)
        
        # Remove some keys
        logger.remove_keys(keys_to_remove)
        
        # Get current keys
        current_keys = logger.get_current_keys()
        
        # Removed keys should not be present
        for key in keys_to_remove:
            if key in initial_keys:  # Only check if key was actually added
                assert key not in current_keys
    
    @given(
        keys=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet=string.ascii_letters),
            values=st.text(min_size=0, max_size=50),
            min_size=1,
            max_size=10
        )
    )
    def test_clear_state_property(self, keys):
        """Property: After clear_state, only default keys should remain."""
        logger = Logger(service="test_service")
        
        # Append custom keys
        logger.append_keys(**keys)
        
        # Clear state
        logger.clear_state()
        
        # Get current keys
        current_keys = logger.get_current_keys()
        
        # Should have service key (default)
        assert "service" in current_keys
        assert current_keys["service"] == "test_service"
        
        # Custom keys should be gone
        for key in keys:
            if key not in ["service", "sampling_rate"]:  # Exclude default keys
                assert key not in current_keys


class TestLogLevelProperties:
    """Test properties related to log level determination."""
    
    @given(
        powertools_level=st.one_of(st.none(), log_levels),
        lambda_level=st.one_of(st.none(), log_levels)
    )
    def test_log_level_precedence_property(self, powertools_level, lambda_level):
        """Property: AWS Lambda ALC level takes precedence over Powertools level."""
        # Set up environment variables
        env_patch = {}
        if lambda_level:
            # Map to the Lambda ALC format
            lambda_level_mapping = {
                'DEBUG': 'Debug',
                'INFO': 'Info', 
                'WARNING': 'Warn',
                'ERROR': 'Error',
                'CRITICAL': 'Fatal'
            }
            env_patch['AWS_LAMBDA_LOG_LEVEL'] = lambda_level_mapping.get(lambda_level, 'Info')
        
        if powertools_level:
            env_patch['POWERTOOLS_LOG_LEVEL'] = powertools_level
        
        with patch.dict(os.environ, env_patch, clear=False):
            logger = Logger(service="test")
            
            # Based on the code precedence:
            # 1. Lambda ALC level wins if set
            # 2. Otherwise Powertools level
            # 3. Otherwise INFO (default)
            
            if lambda_level:
                # Lambda level should be used
                expected_level = getattr(logging, lambda_level)
            elif powertools_level:
                # Powertools level should be used
                expected_level = getattr(logging, powertools_level)
            else:
                # Default is INFO
                expected_level = logging.INFO
            
            assert logger.log_level == expected_level
    
    @given(level=st.one_of(log_levels, log_level_ints))
    def test_set_level_property(self, level):
        """Property: setLevel should correctly set the logger level."""
        logger = Logger(service="test")
        
        # Set the level
        logger.setLevel(level)
        
        # Convert to int if string
        if isinstance(level, str):
            expected_level = getattr(logging, level.upper())
        else:
            expected_level = level
        
        assert logger.log_level == expected_level


class TestChildLoggerProperties:
    """Test properties related to child logger behavior."""
    
    @given(
        parent_service=service_names,
        filename=st.text(min_size=1, max_size=20, alphabet=string.ascii_letters)
    )
    def test_child_logger_naming_property(self, parent_service, filename):
        """Property: Child logger name should be parent_service.filename."""
        with patch('aws_lambda_powertools.logging.logger._get_caller_filename', return_value=filename):
            parent_logger = Logger(service=parent_service)
            child_logger = Logger(service=parent_service, child=True)
            
            # Child logger name should follow the pattern
            expected_name = f"{parent_service}.{filename}"
            assert child_logger.name == expected_name
    
    @given(parent_service=service_names)
    def test_child_logger_handler_inheritance(self, parent_service):
        """Property: Child logger should use parent's handler."""
        # Create parent logger first
        parent_logger = Logger(service=parent_service)
        
        # Create child logger
        with patch('aws_lambda_powertools.logging.logger._get_caller_filename', return_value='test_file'):
            child_logger = Logger(service=parent_service, child=True)
            
            # Child should have access to parent's handler
            # Based on line 328: return getattr(self._logger.parent, LOGGER_ATTRIBUTE_POWERTOOLS_HANDLER, None)
            parent_handler = parent_logger.registered_handler
            child_handler = child_logger.registered_handler
            
            # They should be the same handler object
            assert child_handler == parent_handler


class TestCorrelationIdProperties:
    """Test properties related to correlation ID management."""
    
    @given(correlation_id=st.text(min_size=1, max_size=100))
    def test_correlation_id_round_trip(self, correlation_id):
        """Property: set_correlation_id and get_correlation_id should round-trip correctly."""
        logger = Logger(service="test")
        
        # Set correlation ID
        logger.set_correlation_id(correlation_id)
        
        # Get correlation ID
        retrieved_id = logger.get_correlation_id()
        
        # Should match
        assert retrieved_id == correlation_id
    
    def test_correlation_id_none_removal(self):
        """Property: Setting correlation_id to None should remove it."""
        logger = Logger(service="test")
        
        # Set a correlation ID first
        logger.set_correlation_id("test_id")
        assert logger.get_correlation_id() == "test_id"
        
        # Set to None to remove
        logger.set_correlation_id(None)
        
        # Should be None or not present
        result = logger.get_correlation_id()
        assert result is None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])