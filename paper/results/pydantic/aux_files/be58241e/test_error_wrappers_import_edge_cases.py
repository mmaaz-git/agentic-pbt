import warnings
import sys
from hypothesis import given, strategies as st, assume
import string
from pydantic import error_wrappers
from pydantic.errors import PydanticImportError
from pydantic._migration import MOVED_IN_V2, REMOVED_IN_V2


@given(st.text(alphabet=string.ascii_letters + ":", min_size=1, max_size=30))
def test_colon_in_attribute_names(attr_name):
    """Test attribute names containing colons (which have special meaning in import_string)."""
    # Skip if it's just a colon
    assume(attr_name != ":")
    
    try:
        result = getattr(error_wrappers, attr_name)
        # If successful, it means the attribute exists in the module's __dict__
        # (shouldn't go through import_string for non-migration attributes)
        assert hasattr(error_wrappers, attr_name)
    except (AttributeError, PydanticImportError) as e:
        # Expected for non-existent attributes
        error_msg = str(e)
        # Should not expose internal import_string logic in error messages
        assert "Import strings should" not in error_msg, \
            f"Internal import error leaked for attribute '{attr_name}': {error_msg}"
    except ImportError as e:
        # ImportError should be wrapped in PydanticImportError
        assert False, f"Raw ImportError leaked for attribute '{attr_name}': {e}"


@given(st.text(alphabet=string.ascii_letters + ".:", min_size=1, max_size=50))
def test_dotted_path_attribute_names(attr_name):
    """Test attribute names that look like dotted paths."""
    try:
        result = getattr(error_wrappers, attr_name)
        # If successful, should be in module's __dict__
        assert hasattr(error_wrappers, attr_name)
    except (AttributeError, PydanticImportError):
        # Expected
        pass
    except ImportError as e:
        # Should be wrapped
        assert False, f"Raw ImportError for dotted path '{attr_name}': {e}"


@given(st.text(alphabet=string.ascii_letters + ":", min_size=3, max_size=10)
       .map(lambda s: s if s.count(":") > 1 else "::" + s))
def test_multiple_colons_in_attribute(attr_name):
    """Test attributes with multiple colons."""
    try:
        result = getattr(error_wrappers, attr_name)
        # Should only succeed if it's in __dict__
        assert hasattr(error_wrappers, attr_name)
    except (AttributeError, PydanticImportError):
        # Expected
        pass
    except ImportError as e:
        # Should not leak raw ImportError
        assert False, f"Raw ImportError for multi-colon attribute '{attr_name}': {e}"


def test_empty_string_attribute():
    """Test empty string as attribute name."""
    try:
        result = getattr(error_wrappers, "")
        assert False, "Empty string should not be a valid attribute"
    except AttributeError as e:
        # Expected
        assert "has no attribute ''" in str(e)
    except Exception as e:
        # Should only get AttributeError
        assert False, f"Unexpected exception for empty attribute: {type(e).__name__}: {e}"


def test_whitespace_only_attribute():
    """Test whitespace-only attribute names."""
    for attr_name in [" ", "\t", "\n", "  \t  "]:
        try:
            result = getattr(error_wrappers, attr_name)
            # Might exist (unlikely)
            assert hasattr(error_wrappers, attr_name)
        except AttributeError:
            # Expected
            pass
        except Exception as e:
            assert False, f"Unexpected exception for whitespace attribute '{repr(attr_name)}': {e}"


@given(st.sampled_from([":", "::", ":::", ":attr", "mod:", "mod::"]))
def test_colon_edge_cases(attr_name):
    """Test edge cases with colons in attribute names."""
    try:
        result = getattr(error_wrappers, attr_name)
        # Should only work if in __dict__
        assert hasattr(error_wrappers, attr_name)
    except (AttributeError, PydanticImportError):
        # Expected
        pass
    except ImportError as e:
        # Should be wrapped
        assert False, f"Raw ImportError for colon edge case '{attr_name}': {e}"


def test_manually_inject_moved_mapping():
    """Test what happens if we manually inject a malformed entry into MOVED_IN_V2."""
    # Save original state
    original_moved = MOVED_IN_V2.copy()
    
    try:
        # Add a malformed mapping
        test_cases = [
            ("pydantic.error_wrappers:TestAttr1", ":::"),  # Invalid import path
            ("pydantic.error_wrappers:TestAttr2", ""),  # Empty import path
            ("pydantic.error_wrappers:TestAttr3", "nonexistent.module:attr"),  # Non-existent module
        ]
        
        for old_path, new_path in test_cases:
            MOVED_IN_V2[old_path] = new_path
            
            # Try to access the attribute
            attr_name = old_path.split(":")[1]
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    result = getattr(error_wrappers, attr_name)
                    # Should not succeed with invalid import paths
                    assert False, f"Should fail for invalid import path '{new_path}'"
            except (PydanticImportError, AttributeError):
                # These are acceptable errors
                pass
            except Exception as e:
                # Check if it's an ImportError that wasn't properly wrapped
                if isinstance(e, ImportError):
                    assert False, f"Raw ImportError for invalid mapping '{new_path}': {e}"
                # Other exceptions might be acceptable depending on the invalid path
                pass
            finally:
                # Clean up this entry
                del MOVED_IN_V2[old_path]
    finally:
        # Restore original state
        MOVED_IN_V2.clear()
        MOVED_IN_V2.update(original_moved)


def test_manually_inject_removed_mapping():
    """Test edge cases with REMOVED_IN_V2."""
    # Save original state
    original_removed = REMOVED_IN_V2.copy()
    
    try:
        # Add some test entries
        test_attrs = ["", " ", ":", "::", "Test.Attr", "Test:Attr"]
        
        for attr_name in test_attrs:
            REMOVED_IN_V2.add(f"pydantic.error_wrappers:{attr_name}")
            
            try:
                result = getattr(error_wrappers, attr_name)
                assert False, f"Should raise PydanticImportError for removed '{attr_name}'"
            except PydanticImportError as e:
                # Expected
                assert "has been removed in V2" in str(e)
            except AttributeError as e:
                # Might happen if the attribute name is invalid
                if attr_name in ["", " ", ":"]:
                    # These might be handled differently
                    pass
                else:
                    assert False, f"Got AttributeError instead of PydanticImportError for '{attr_name}': {e}"
            finally:
                # Clean up
                REMOVED_IN_V2.discard(f"pydantic.error_wrappers:{attr_name}")
    finally:
        # Restore original state
        REMOVED_IN_V2.clear()
        REMOVED_IN_V2.update(original_removed)


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=20))
def test_attribute_name_normalization(base_name):
    """Test if attribute names are normalized in any way."""
    # Try with leading/trailing whitespace
    padded_name = f"  {base_name}  "
    
    try:
        result_padded = getattr(error_wrappers, padded_name)
        # If it works, check if it's the same as without padding
        try:
            result_normal = getattr(error_wrappers, base_name)
            # Are they the same?
            assert result_padded == result_normal, \
                "Padded and normal attribute access returned different results"
        except AttributeError:
            # Padded worked but normal didn't - interesting!
            pass
    except AttributeError:
        # Expected for non-existent attributes
        pass


def test_validation_error_multiple_access_patterns():
    """Test different ways to access ValidationError."""
    results = []
    
    # Method 1: Direct getattr
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r1 = getattr(error_wrappers, "ValidationError")
        results.append(("getattr", r1))
    
    # Method 2: Using __getattr__ directly
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r2 = error_wrappers.__getattr__("ValidationError")
        results.append(("__getattr__", r2))
    
    # Method 3: Via import
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from pydantic.error_wrappers import ValidationError as r3
        results.append(("import", r3))
    
    # All should return the same object
    first_obj = results[0][1]
    for method, obj in results[1:]:
        assert obj is first_obj, f"Method {method} returned different object"