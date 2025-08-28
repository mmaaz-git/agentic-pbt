#!/usr/bin/env python3
"""Property-based tests for trino.logging module"""

import logging
import sys
import os

# Add the trino package to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import trino.logging


@given(st.text(min_size=1))
def test_get_logger_returns_logger_instance(name):
    """Test that get_logger always returns a logging.Logger instance"""
    logger = trino.logging.get_logger(name)
    assert isinstance(logger, logging.Logger)


@given(st.text(min_size=1))
def test_get_logger_returns_correct_name(name):
    """Test that the logger returned has the name provided"""
    logger = trino.logging.get_logger(name)
    assert logger.name == name


@given(st.text(min_size=1))
def test_get_logger_without_level_preserves_existing(name):
    """Test that when log_level is None, the logger's level is not modified"""
    # First, get a logger and set a specific level
    logger1 = logging.getLogger(name)
    original_level = logging.WARNING
    logger1.setLevel(original_level)
    
    # Now get it through get_logger without specifying level
    logger2 = trino.logging.get_logger(name)
    
    # The level should be preserved
    assert logger2.level == original_level
    assert logger1 is logger2  # Should be the same object


@given(
    st.text(min_size=1),
    st.sampled_from([
        logging.NOTSET,
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
        10, 20, 30, 40, 50  # numeric values
    ])
)
def test_get_logger_with_level_sets_level(name, log_level):
    """Test that when log_level is provided, it sets that level on the logger"""
    logger = trino.logging.get_logger(name, log_level)
    assert logger.level == log_level


@given(
    st.text(min_size=1),
    st.one_of(st.none(), st.integers(min_value=0, max_value=100))
)
def test_get_logger_idempotence(name, log_level):
    """Test that calling get_logger multiple times with same args returns same logger"""
    logger1 = trino.logging.get_logger(name, log_level)
    logger2 = trino.logging.get_logger(name, log_level)
    
    # Python's logging module returns the same logger instance for the same name
    assert logger1 is logger2
    
    # And they should have the same level
    assert logger1.level == logger2.level


@given(st.text(min_size=1))
def test_logger_hierarchy_preserved(name):
    """Test that logger hierarchy is preserved (dots create parent-child relationships)"""
    # Create loggers with hierarchical names
    if '.' in name:
        parent_name = name.rsplit('.', 1)[0]
        parent_logger = trino.logging.get_logger(parent_name)
        child_logger = trino.logging.get_logger(name)
        
        # Child should have parent in its hierarchy
        assert child_logger.parent.name == parent_name or child_logger.parent.name == 'root'


@given(st.text(min_size=1))
def test_trino_root_logger_exists_and_has_correct_level(name):
    """Test that the trino_root_logger is properly initialized"""
    # The module creates a root logger for 'trino' with LEVEL
    assert hasattr(trino.logging, 'trino_root_logger')
    assert isinstance(trino.logging.trino_root_logger, logging.Logger)
    assert trino.logging.trino_root_logger.name == 'trino'
    assert trino.logging.trino_root_logger.level == trino.logging.LEVEL


@given(
    st.text(min_size=1),
    st.integers(min_value=-1000, max_value=1000)
)
def test_get_logger_handles_arbitrary_integer_levels(name, log_level):
    """Test that get_logger handles arbitrary integer log levels"""
    logger = trino.logging.get_logger(name, log_level)
    assert logger.level == log_level


@given(st.just(""))
def test_empty_name_handling(name):
    """Test how get_logger handles empty strings"""
    logger = trino.logging.get_logger(name)
    assert isinstance(logger, logging.Logger)
    assert logger.name == "root"  # Empty string gives root logger