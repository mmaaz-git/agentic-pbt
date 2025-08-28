import sys
sys.path.append('/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from rpdk.java.utils import (
    safe_reserved, 
    safe_reserved_hook_target, 
    LANGUAGE_KEYWORDS,
    HOOK_TARGET_KEYWORDS,
    validate_namespace,
    validate_codegen_model
)
from rpdk.java.resolver import translate_type, PRIMITIVE_TYPES, UNDEFINED
from rpdk.core.jsonutils.resolver import ResolvedType, ContainerType, FORMAT_DEFAULT
from rpdk.core.exceptions import WizardValidationError
import pytest


# Test potential mutation bugs in safe_reserved
@given(st.text(min_size=1, max_size=50))
def test_safe_reserved_no_mutation(token):
    """safe_reserved should not mutate its input"""
    original = token
    result = safe_reserved(token)
    # Ensure the original string wasn't mutated
    assert token == original


# Test validate_namespace with tricky edge cases
def test_validate_namespace_underscore_only_segments():
    """Segments with only underscores should fail pattern match"""
    validator = validate_namespace(("default",))
    
    # Single underscore doesn't match pattern [_a-z][_a-z0-9]+
    with pytest.raises(WizardValidationError):
        validator("_")
    
    # Multiple underscores also fail
    with pytest.raises(WizardValidationError):
        validator("__")
    
    with pytest.raises(WizardValidationError):
        validator("com.__.test")


def test_validate_namespace_underscore_followed_by_number():
    """_0, _1, etc. should fail the pattern"""
    validator = validate_namespace(("default",))
    
    # Pattern is [_a-z][_a-z0-9]+ which requires at least 2 chars
    # _0 is only 2 chars but should match the pattern
    # Let's test this
    with pytest.raises(WizardValidationError):
        validator("_0")  # Only 2 chars, but might fail minimum length


def test_validate_namespace_boundary_keywords():
    """Test keywords at package boundaries"""
    validator = validate_namespace(("default",))
    
    # Exact keyword match should fail
    with pytest.raises(WizardValidationError, match="reserved keyword"):
        validator("class")
    
    # Keyword as part of larger segment should pass if valid
    result = validator("classy")  # Has 6 chars, starts with letter, all lowercase
    assert result == ("classy",)


# Test translate_type with invalid container types
def test_translate_type_with_none_type():
    """Test translate_type with None as inner type"""
    # This might cause issues if not handled properly
    resolved = ResolvedType(ContainerType.LIST, None)
    
    try:
        result = translate_type(resolved)
        # If it doesn't crash, check the result makes sense
        assert "List<" in result
    except (AttributeError, TypeError) as e:
        # This would be a bug - the function should handle None gracefully
        pytest.fail(f"translate_type failed with None inner type: {e}")


# Test for case sensitivity issues
def test_safe_reserved_null_keyword():
    """Test that 'null' (Java literal) is not treated as keyword"""
    # 'null' is a literal in Java, not in LANGUAGE_KEYWORDS
    result = safe_reserved("null")
    assert result == "null"  # Should be unchanged
    
    # Same for 'true' and 'false'
    assert safe_reserved("true") == "true"
    assert safe_reserved("false") == "false"


# Test namespace validation with maximum nesting
@given(st.integers(min_value=1, max_value=100))
def test_validate_namespace_deep_nesting(depth):
    """Test deeply nested package names"""
    validator = validate_namespace(("default",))
    
    # Create a valid deeply nested package
    segments = ["com"] + [f"level{i}" for i in range(depth)]
    namespace_str = ".".join(segments)
    
    if depth > 50:  # Arbitrary limit for testing
        # Very deep nesting might have practical limits
        try:
            result = validator(namespace_str)
            assert len(result) == len(segments)
        except Exception:
            # If there's a depth limit, that's fine
            pass
    else:
        result = validator(namespace_str)
        assert result == tuple(segments)


# Test translate_type recursion depth
def test_translate_type_deep_nesting():
    """Test deeply nested container types"""
    # Create a deeply nested type: List<List<List<...>>>
    inner = ResolvedType(ContainerType.PRIMITIVE, "string")
    
    for _ in range(10):  # 10 levels of nesting
        inner = ResolvedType(ContainerType.LIST, inner)
    
    result = translate_type(inner)
    
    # Check that we have the right number of angle brackets
    assert result.count("<") == 10
    assert result.count(">") == 10
    assert "String" in result


# Test boundary between hook keywords and language keywords
def test_hook_target_properties_keyword():
    """'properties' should be treated as keyword only for hook targets"""
    # For regular safe_reserved, 'properties' is NOT a keyword
    assert safe_reserved("properties") == "properties"
    
    # For hook target, 'properties' IS a keyword
    assert safe_reserved_hook_target("properties") == "properties_"


# Test with actual Java reserved words not in the list
def test_missing_java_keywords():
    """Check if any Java keywords might be missing from LANGUAGE_KEYWORDS"""
    # Some Java keywords that should be in the list
    important_keywords = [
        "abstract", "assert", "boolean", "break", "byte", "case", "catch",
        "char", "class", "const", "continue", "default", "do", "double",
        "else", "enum", "extends", "final", "finally", "float", "for",
        "goto", "if", "implements", "import", "instanceof", "int",
        "interface", "long", "native", "new", "package", "private",
        "protected", "public", "return", "short", "static", "strictfp",
        "super", "switch", "synchronized", "this", "throw", "throws",
        "transient", "try", "void", "volatile", "while"
    ]
    
    for keyword in important_keywords:
        assert keyword in LANGUAGE_KEYWORDS, f"Missing Java keyword: {keyword}"


# Test translate_type with mixed valid/invalid formats
@given(st.sampled_from(["int32", "int64", "invalid", "", None]))
def test_translate_type_integer_formats(format_type):
    """Test integer type with various format specifications"""
    if format_type is None:
        resolved = ResolvedType(ContainerType.PRIMITIVE, "integer")
    else:
        resolved = ResolvedType(ContainerType.PRIMITIVE, "integer", format_type)
    
    result = translate_type(resolved)
    
    if format_type == "int32":
        assert result == "Integer"
    elif format_type == "int64":
        assert result == "Long"
    else:
        # Should default to Integer for invalid/missing formats
        assert result == "Integer"


# Test empty namespace validation
def test_validate_namespace_empty_string():
    """Empty string should return default namespace"""
    validator = validate_namespace(("com", "example", "default"))
    result = validator("")
    assert result == ("com", "example", "default")


# Test codegen model with padded values
@given(st.sampled_from([" 1", "1 ", " 1 ", "\t1", "1\n", " 2 "]))
def test_validate_codegen_model_with_whitespace_padding(value):
    """Values with whitespace padding should be rejected"""
    validator = validate_codegen_model("1")
    
    # The regex pattern is ^[1-2]$ which shouldn't match padded values
    with pytest.raises(WizardValidationError, match="Invalid selection"):
        validator(value)


# Property: safe_reserved should preserve string length relationship
@given(st.text(min_size=0, max_size=100))
def test_safe_reserved_length_property(token):
    """safe_reserved output should be >= input length"""
    result = safe_reserved(token)
    assert len(result) >= len(token)
    
    # If it's a keyword, it should be exactly 1 char longer
    if token in LANGUAGE_KEYWORDS:
        assert len(result) == len(token) + 1


# Test potential integer overflow in validate_codegen_model
@given(st.sampled_from(["99999999999999999999", "-99999999999999999999", "1e308"]))
def test_validate_codegen_model_large_numbers(value):
    """Large numbers should be rejected"""
    validator = validate_codegen_model("1")
    
    with pytest.raises(WizardValidationError, match="Invalid selection"):
        validator(value)