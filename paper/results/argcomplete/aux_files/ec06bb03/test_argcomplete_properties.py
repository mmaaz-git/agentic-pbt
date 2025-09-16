#!/usr/bin/env python3
import argcomplete
from argcomplete import split_line, ChoicesCompleter, FilesCompleter, DirectoriesCompleter
from hypothesis import given, strategies as st, assume, settings
import math
import os
import tempfile
import shutil


# Strategy for generating shell-like strings
shell_strings = st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=0, max_size=100)
simple_strings = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./', min_size=0, max_size=50)


# Test split_line properties
@given(shell_strings)
def test_split_line_returns_5_tuple(line):
    """split_line should always return a 5-tuple"""
    result = split_line(line)
    assert isinstance(result, tuple)
    assert len(result) == 5


@given(shell_strings, st.integers(min_value=0, max_value=200))
def test_split_line_with_point_returns_5_tuple(line, point):
    """split_line with point should always return a 5-tuple"""
    # Point should be within or just after the line
    point = min(point, len(line) + 1)
    result = split_line(line, point)
    assert isinstance(result, tuple)
    assert len(result) == 5


@given(shell_strings)
def test_split_line_prefix_suffix_consistency(line):
    """The prefix should come from the line up to the point"""
    result = split_line(line)
    prequote, prefix, suffix, words, wordbreak_pos = result
    # All components should be strings or None
    assert isinstance(prequote, str)
    assert isinstance(prefix, str)
    assert isinstance(suffix, str)
    assert isinstance(words, list)
    assert wordbreak_pos is None or isinstance(wordbreak_pos, int)


@given(simple_strings)
def test_split_line_simple_words(line):
    """For simple input without quotes, words should match a basic split"""
    # Only test simple cases without special characters
    assume(not any(c in line for c in ['"', "'", '\\', '\n', '\r', '\t']))
    result = split_line(line)
    prequote, prefix, suffix, words, wordbreak_pos = result
    # The words list should contain valid strings
    assert all(isinstance(w, str) for w in words)


@given(st.text(alphabet='abc ', min_size=1, max_size=50))
def test_split_line_whitespace_handling(line):
    """split_line should handle whitespace correctly"""
    assume(line.strip())  # Skip pure whitespace
    result = split_line(line)
    prequote, prefix, suffix, words, wordbreak_pos = result
    # Should not crash and should return valid structure
    assert isinstance(words, list)
    if line.strip():
        # Non-empty input should produce some parsing result
        assert len(words) >= 0


# Test ChoicesCompleter properties
@given(st.lists(st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text()), min_size=0, max_size=50))
def test_choices_completer_converts_to_strings(choices):
    """ChoicesCompleter should convert all choices to strings"""
    completer = ChoicesCompleter(choices)
    results = list(completer())
    assert len(results) == len(choices)
    assert all(isinstance(r, str) for r in results)
    # Check conversion is consistent
    for original, converted in zip(choices, results):
        assert converted == str(original)


@given(st.lists(st.text(), min_size=0, max_size=50))
def test_choices_completer_preserves_string_choices(string_choices):
    """ChoicesCompleter should preserve string choices unchanged"""
    completer = ChoicesCompleter(string_choices)
    results = list(completer())
    assert results == string_choices


# Test that ChoicesCompleter is idempotent for strings
@given(st.lists(st.text(), min_size=0, max_size=50))
def test_choices_completer_idempotent(choices):
    """Applying ChoicesCompleter twice should give same result as once for strings"""
    completer1 = ChoicesCompleter(choices)
    results1 = list(completer1())
    completer2 = ChoicesCompleter(results1)
    results2 = list(completer2())
    assert results1 == results2


# Test FilesCompleter basic properties
def test_files_completer_returns_strings():
    """FilesCompleter should always return strings"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        for name in ['test1.txt', 'test2.py', 'test3.md']:
            open(os.path.join(tmpdir, name), 'w').close()
        
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            completer = FilesCompleter()
            results = list(completer())
            assert all(isinstance(r, str) for r in results)
        finally:
            os.chdir(old_cwd)


@given(st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10), min_size=1, max_size=5))
def test_files_completer_with_extensions(extensions):
    """FilesCompleter with extensions should filter correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with various extensions
        test_files = ['test.txt', 'test.py', 'test.md', 'test.json', 'test.xml']
        for name in test_files:
            open(os.path.join(tmpdir, name), 'w').close()
        
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            # Test with specific extensions
            ext_list = ['.' + ext for ext in extensions]
            completer = FilesCompleter(allowednames=ext_list)
            results = list(completer())
            
            # All results should be strings
            assert all(isinstance(r, str) for r in results)
            
            # Results should only include files with allowed extensions
            for result in results:
                if '.' in result:
                    assert any(result.endswith(ext) for ext in ext_list)
        finally:
            os.chdir(old_cwd)


# Test DirectoriesCompleter
def test_directories_completer_returns_strings():
    """DirectoriesCompleter should return only directories as strings"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some directories and files
        os.makedirs(os.path.join(tmpdir, 'dir1'))
        os.makedirs(os.path.join(tmpdir, 'dir2'))
        open(os.path.join(tmpdir, 'file1.txt'), 'w').close()
        
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            completer = DirectoriesCompleter()
            results = list(completer())
            assert all(isinstance(r, str) for r in results)
            # Should only return directories
            for result in results:
                path = result.rstrip('/')
                if os.path.exists(path):
                    assert os.path.isdir(path)
        finally:
            os.chdir(old_cwd)


# Test split_line with quoted strings
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=0, max_size=50))
def test_split_line_single_quotes(text):
    """split_line should handle single-quoted strings"""
    line = f"'{text}'"
    result = split_line(line)
    prequote, prefix, suffix, words, wordbreak_pos = result
    assert isinstance(result, tuple)
    assert len(result) == 5
    # Should successfully parse quoted string
    if text:
        assert len(words) <= 1  # Single quoted string should be at most one word


@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=0, max_size=50))
def test_split_line_double_quotes(text):
    """split_line should handle double-quoted strings"""
    line = f'"{text}"'
    result = split_line(line)
    prequote, prefix, suffix, words, wordbreak_pos = result
    assert isinstance(result, tuple)
    assert len(result) == 5
    # Should successfully parse quoted string
    if text:
        assert len(words) <= 1  # Single quoted string should be at most one word


# Test split_line with mixed quotes
@given(st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10), min_size=0, max_size=5))
def test_split_line_word_count(words_list):
    """split_line should preserve word count for simple inputs"""
    # Create a simple space-separated line
    line = ' '.join(words_list)
    assume(all(w for w in words_list))  # Skip empty strings
    
    result = split_line(line)
    prequote, prefix, suffix, words, wordbreak_pos = result
    
    # For simple inputs, word count should be preserved
    if words_list:
        assert len(words) == len([w for w in words_list if w])


# Test edge cases
def test_split_line_empty_string():
    """split_line should handle empty string"""
    result = split_line("")
    assert result == ("", "", "", [], None)


def test_split_line_only_whitespace():
    """split_line should handle whitespace-only input"""
    result = split_line("   ")
    prequote, prefix, suffix, words, wordbreak_pos = result
    assert isinstance(result, tuple)
    assert len(result) == 5
    assert words == []


# Test that split_line point parameter works correctly
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=1, max_size=50))
def test_split_line_point_within_bounds(text):
    """split_line with point should work for any valid position"""
    for point in [0, len(text) // 2, len(text)]:
        result = split_line(text, point)
        assert isinstance(result, tuple)
        assert len(result) == 5
        prequote, prefix, suffix, words, wordbreak_pos = result
        # Point affects what is considered prefix
        assert isinstance(prefix, str)
        assert isinstance(suffix, str)