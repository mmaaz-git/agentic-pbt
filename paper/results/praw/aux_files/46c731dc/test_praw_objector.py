"""Property-based tests for praw.objector module using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import praw
from praw.objector import Objector
from praw.util.snake import camel_to_snake, snake_case_keys
from praw.exceptions import ClientException, RedditAPIException
import re


# Strategy for generating camelCase-like strings
camel_case_str = st.text(
    alphabet=st.characters(whitelist_categories=("L", "Nd")), 
    min_size=1,
    max_size=50
).filter(lambda s: s[0].isalpha())  # Must start with letter

# Strategy for generating dict keys (valid Python identifiers)
dict_key_str = st.text(
    alphabet=st.characters(whitelist_categories=("L", "Nd"), whitelist_characters="_"),
    min_size=1,
    max_size=30
).filter(lambda s: s[0].isalpha() or s[0] == '_')


class TestSnakeCase:
    """Test properties of snake case conversion functions."""
    
    @given(camel_case_str)
    def test_camel_to_snake_lowercase(self, text):
        """camel_to_snake should always return lowercase strings."""
        result = camel_to_snake(text)
        assert result.islower() or not any(c.isalpha() for c in result)
    
    @given(camel_case_str)
    def test_camel_to_snake_idempotent_on_snake_case(self, text):
        """camel_to_snake should be idempotent for already snake_case strings."""
        # Convert once to snake case
        snake = camel_to_snake(text)
        # Converting again should give same result
        double_snake = camel_to_snake(snake)
        assert snake == double_snake
    
    @given(st.dictionaries(dict_key_str, st.integers()))
    def test_snake_case_keys_preserves_dict_size(self, dictionary):
        """snake_case_keys should preserve the number of keys in dictionary."""
        result = snake_case_keys(dictionary)
        # Note: This could fail if two different camelCase keys map to same snake_case
        # Let's check if all original keys are unique when converted
        converted_keys = [camel_to_snake(k) for k in dictionary.keys()]
        if len(converted_keys) == len(set(converted_keys)):
            # Only test if no key collisions
            assert len(result) == len(dictionary)
    
    @given(st.dictionaries(dict_key_str, st.integers()))
    def test_snake_case_keys_all_lowercase(self, dictionary):
        """All keys in snake_case_keys output should be lowercase."""
        result = snake_case_keys(dictionary)
        for key in result.keys():
            assert key.islower() or not any(c.isalpha() for c in key)
    
    @given(st.dictionaries(dict_key_str, st.integers()))
    def test_snake_case_keys_deterministic(self, dictionary):
        """snake_case_keys should be deterministic."""
        result1 = snake_case_keys(dictionary)
        result2 = snake_case_keys(dictionary)
        assert result1 == result2


class TestObjectorErrorHandling:
    """Test error handling properties of Objector class."""
    
    @given(st.lists(st.integers()))
    def test_parse_error_returns_none_for_lists(self, data):
        """parse_error should always return None for list inputs."""
        result = Objector.parse_error(data)
        assert result is None
    
    @given(st.dictionaries(
        st.text(min_size=1, max_size=10).filter(lambda x: x != "json"),
        st.integers()
    ))
    def test_parse_error_returns_none_without_json_key(self, data):
        """parse_error should return None if 'json' key is missing."""
        result = Objector.parse_error(data)
        assert result is None
    
    @given(st.dictionaries(st.text(min_size=1, max_size=10), st.integers()))
    def test_parse_error_returns_none_without_errors_path(self, data):
        """parse_error should return None if 'json.errors' path is missing."""
        # Ensure we don't accidentally have the right structure
        if "json" in data:
            if isinstance(data["json"], dict) and "errors" in data["json"]:
                return  # Skip this case
        result = Objector.parse_error(data) 
        assert result is None
    
    def test_parse_error_raises_on_empty_errors_list(self):
        """parse_error should raise ClientException when errors list is empty."""
        data = {"json": {"errors": []}}
        try:
            Objector.parse_error(data)
            assert False, "Should have raised ClientException"
        except ClientException as e:
            assert "successful error response" in str(e)
    
    @given(st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20),  # error type
            st.text(min_size=0, max_size=50),  # message
            st.text(min_size=0, max_size=20)   # field
        ),
        min_size=1,
        max_size=5
    ))
    def test_parse_error_returns_exception_for_valid_errors(self, errors_data):
        """parse_error should return RedditAPIException for valid error structure."""
        # Build proper error structure 
        errors = [[err[0], err[1], err[2]] for err in errors_data]
        data = {"json": {"errors": errors}}
        result = Objector.parse_error(data)
        assert isinstance(result, RedditAPIException)


class TestObjectorObjectify:
    """Test objectify method properties."""
    
    def test_objectify_none_returns_none(self):
        """objectify should return None when given None."""
        reddit = praw.Reddit(
            client_id="test",
            client_secret="test", 
            user_agent="test"
        )
        objector = Objector(reddit)
        result = objector.objectify(None)
        assert result is None
    
    @given(st.booleans())
    def test_objectify_bool_returns_same_bool(self, value):
        """objectify should return the same boolean when given a boolean."""
        reddit = praw.Reddit(
            client_id="test",
            client_secret="test",
            user_agent="test"
        )
        objector = Objector(reddit)
        result = objector.objectify(value)
        assert result is value
    
    @given(st.lists(st.none() | st.booleans() | st.integers(), max_size=20))
    def test_objectify_list_preserves_length(self, data):
        """objectify should preserve list length for simple data types."""
        reddit = praw.Reddit(
            client_id="test",
            client_secret="test",
            user_agent="test"
        )
        objector = Objector(reddit)
        result = objector.objectify(data)
        assert isinstance(result, list)
        assert len(result) == len(data)
    
    @given(st.lists(st.booleans(), min_size=1, max_size=20))
    def test_objectify_list_preserves_bool_values(self, data):
        """objectify should preserve boolean values in lists."""
        reddit = praw.Reddit(
            client_id="test",
            client_secret="test",
            user_agent="test"
        )
        objector = Objector(reddit)
        result = objector.objectify(data)
        assert result == data
    
    @given(st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers() | st.text() | st.none(),
        max_size=10
    ))
    def test_objectify_dict_returns_dict_or_object(self, data):
        """objectify should handle dict inputs without crashing."""
        reddit = praw.Reddit(
            client_id="test",
            client_secret="test",
            user_agent="test"
        )
        objector = Objector(reddit)
        # This should not raise an exception for arbitrary dicts
        result = objector.objectify(data)
        # Result should be something (dict, object, or transformed data)
        assert result is not None or data == {}


class TestCamelToSnakeEdgeCases:
    """Test edge cases and special patterns in camel_to_snake conversion."""
    
    def test_consecutive_capitals(self):
        """Test handling of consecutive capital letters."""
        assert camel_to_snake("HTTPSConnection") == "https_connection"
        assert camel_to_snake("XMLParser") == "xml_parser"
        assert camel_to_snake("IOError") == "io_error"
    
    def test_numbers_in_names(self):
        """Test handling of numbers in variable names."""
        assert camel_to_snake("base64Encode") == "base64_encode"
        assert camel_to_snake("testCase1") == "test_case1"
        assert camel_to_snake("md5Hash") == "md5_hash"
    
    def test_already_snake_case(self):
        """Test that already snake_case strings are preserved."""
        assert camel_to_snake("already_snake_case") == "already_snake_case"
        assert camel_to_snake("lower_case_name") == "lower_case_name"
    
    @given(st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=2, max_size=10))
    def test_all_uppercase(self, text):
        """Test conversion of all uppercase strings."""
        result = camel_to_snake(text)
        assert result == text.lower()