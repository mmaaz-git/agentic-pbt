"""Property-based tests for praw.endpoints module."""

import re
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from praw.endpoints import API_PATH


def test_all_values_are_non_empty_strings():
    """All endpoint paths should be non-empty strings."""
    for endpoint_name, path in API_PATH.items():
        assert isinstance(path, str), f"{endpoint_name} path is not a string"
        assert len(path) > 0, f"{endpoint_name} has empty path"


def test_all_keys_are_non_empty_strings():
    """All endpoint names should be non-empty strings."""
    for endpoint_name in API_PATH.keys():
        assert isinstance(endpoint_name, str), f"Key {endpoint_name} is not a string"
        assert len(endpoint_name) > 0, f"Found empty endpoint name"


def test_valid_placeholder_format():
    """All placeholders in paths should follow {identifier} format."""
    placeholder_pattern = re.compile(r'\{([^}]+)\}')
    identifier_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    
    for endpoint_name, path in API_PATH.items():
        placeholders = placeholder_pattern.findall(path)
        for placeholder in placeholders:
            assert identifier_pattern.match(placeholder), \
                f"Invalid placeholder '{placeholder}' in {endpoint_name}: {path}"


def test_no_duplicate_paths():
    """Each endpoint path should be unique to avoid routing conflicts."""
    paths = list(API_PATH.values())
    unique_paths = set(paths)
    
    if len(paths) != len(unique_paths):
        # Find duplicates
        seen = set()
        duplicates = {}
        for name, path in API_PATH.items():
            if path in seen:
                if path not in duplicates:
                    duplicates[path] = []
                duplicates[path].append(name)
            seen.add(path)
        
        # Find the first occurrence of each duplicate
        for path, names in duplicates.items():
            first_occurrence = None
            for name, p in API_PATH.items():
                if p == path:
                    if first_occurrence is None:
                        first_occurrence = name
                        duplicates[path].insert(0, first_occurrence)
                    break
        
        assert False, f"Found duplicate paths: {duplicates}"


def test_path_format_consistency():
    """Paths should not contain protocol or absolute URLs."""
    for endpoint_name, path in API_PATH.items():
        assert not path.startswith('http://'), \
            f"{endpoint_name} contains http:// protocol"
        assert not path.startswith('https://'), \
            f"{endpoint_name} contains https:// protocol"
        assert not path.startswith('//'), \
            f"{endpoint_name} starts with // (protocol-relative URL)"


def test_no_invalid_url_characters():
    """Paths should not contain characters invalid in URLs."""
    # These characters are generally invalid in URL paths (excluding query strings)
    invalid_chars = ['<', '>', '"', ' ', '\n', '\r', '\t', '\\']
    
    for endpoint_name, path in API_PATH.items():
        for char in invalid_chars:
            assert char not in path, \
                f"{endpoint_name} contains invalid character '{repr(char)}' in path: {path}"


def test_consistent_placeholder_usage():
    """Common placeholders should be used consistently across endpoints."""
    placeholder_pattern = re.compile(r'\{([^}]+)\}')
    
    # Collect all placeholders
    placeholder_usage = {}
    for endpoint_name, path in API_PATH.items():
        placeholders = placeholder_pattern.findall(path)
        for placeholder in placeholders:
            if placeholder not in placeholder_usage:
                placeholder_usage[placeholder] = []
            placeholder_usage[placeholder].append((endpoint_name, path))
    
    # Check common placeholders are used in consistent contexts
    # For example, {subreddit} should always represent a subreddit
    for placeholder, usages in placeholder_usage.items():
        if placeholder == 'subreddit':
            for endpoint_name, path in usages:
                # {subreddit} should typically appear in r/{subreddit} pattern
                assert 'r/{subreddit}' in path or '/{subreddit}/' in path or path.endswith('/{subreddit}'), \
                    f"Inconsistent use of {{subreddit}} in {endpoint_name}: {path}"


def test_api_path_is_dictionary():
    """API_PATH should be a dictionary."""
    assert isinstance(API_PATH, dict), "API_PATH is not a dictionary"
    assert len(API_PATH) > 0, "API_PATH is empty"


def test_endpoint_names_follow_convention():
    """Endpoint names should follow snake_case convention."""
    snake_case_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
    
    for endpoint_name in API_PATH.keys():
        assert snake_case_pattern.match(endpoint_name), \
            f"Endpoint name '{endpoint_name}' doesn't follow snake_case convention"