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


# Edge case 1: validate_namespace with dots and empty segments
@given(st.text(min_size=0, max_size=100))
@example(".")
@example("..")
@example("com..example")
@example(".com.example")
@example("com.example.")
@example("com.example..")
def test_validate_namespace_empty_segments(namespace_str):
    """Empty segments in namespace should be rejected"""
    validator = validate_namespace(("default",))
    
    if ".." in namespace_str or namespace_str.startswith(".") or namespace_str.endswith("."):
        if namespace_str:  # Non-empty string with these patterns
            with pytest.raises(WizardValidationError):
                validator(namespace_str)


# Edge case 2: validate_namespace with single character segments
@given(st.lists(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_0123456789", min_size=1, max_size=1), min_size=1, max_size=5))
def test_validate_namespace_single_char_segments(segments):
    """Single character segments should be rejected if they don't match pattern"""
    validator = validate_namespace(("default",))
    namespace_str = ".".join(segments)
    
    # Pattern requires at least 2 characters: [_a-z][_a-z0-9]+
    # So single character segments should fail
    with pytest.raises(WizardValidationError):
        validator(namespace_str)


# Edge case 3: translate_type with undefined type
def test_translate_type_undefined():
    """UNDEFINED type should translate to Object"""
    resolved = ResolvedType(ContainerType.PRIMITIVE, UNDEFINED)
    result = translate_type(resolved)
    assert result == "Object"


# Edge case 4: translate_type with unknown format
@given(st.text(min_size=1, max_size=20).filter(lambda x: x not in ["default", "int32", "int64"]))
def test_translate_type_unknown_format(format_str):
    """Unknown formats should fall back to default"""
    resolved = ResolvedType(ContainerType.PRIMITIVE, "integer", format_str)
    result = translate_type(resolved)
    # Should fall back to default Integer for unknown formats
    assert result == "Integer"


# Edge case 5: validate_namespace with numbers at start
@given(st.text(alphabet="0123456789", min_size=1, max_size=5))
def test_validate_namespace_number_start(number_prefix):
    """Segments starting with numbers should be rejected"""
    validator = validate_namespace(("default",))
    namespace_str = f"{number_prefix}package"
    
    with pytest.raises(WizardValidationError, match="begin with a lower case letter"):
        validator(namespace_str)


# Edge case 6: Empty string handling
def test_safe_reserved_empty_string():
    """Empty string should pass through unchanged"""
    # Based on the function, it only checks membership in LANGUAGE_KEYWORDS
    # Empty string is not a keyword, so should be unchanged
    result = safe_reserved("")
    assert result == ""


def test_safe_reserved_hook_target_empty_string():
    """Empty string should pass through unchanged for hook target"""
    result = safe_reserved_hook_target("")
    assert result == ""


# Edge case 7: validate_codegen_model with whitespace
@given(st.text(alphabet=" \t\n\r", min_size=1, max_size=10))
def test_validate_codegen_model_whitespace(whitespace):
    """Whitespace-only input should be rejected"""
    validator = validate_codegen_model("1")
    
    with pytest.raises(WizardValidationError, match="Invalid selection"):
        validator(whitespace)


# Edge case 8: translate_type with MULTIPLE container
def test_translate_type_multiple_container():
    """MULTIPLE container type should translate to Object"""
    resolved = ResolvedType(ContainerType.MULTIPLE, "anything")
    result = translate_type(resolved)
    assert result == "Object"


# Edge case 9: translate_type with MODEL container
def test_translate_type_model_container():
    """MODEL container should return the model name directly"""
    model_name = "MyCustomModel"
    resolved = ResolvedType(ContainerType.MODEL, model_name)
    result = translate_type(resolved)
    assert result == model_name


# Edge case 10: Complex nested containers
def test_translate_type_map_of_lists():
    """Map of lists should produce Map<String, List<Type>>"""
    inner = ResolvedType(ContainerType.PRIMITIVE, "string")
    list_type = ResolvedType(ContainerType.LIST, inner)
    map_type = ResolvedType(ContainerType.DICT, list_type)
    result = translate_type(map_type)
    assert result == "Map<String, List<String>>"


# Edge case 11: Special characters in safe_reserved
@given(st.text(alphabet="!@#$%^&*()+={}[]|\\:;\"'<>,.?/~`", min_size=1, max_size=20))
def test_safe_reserved_special_chars(special_str):
    """Special characters should pass through unchanged (not Java keywords)"""
    result = safe_reserved(special_str)
    assert result == special_str


# Edge case 12: validate_namespace with uppercase in middle
def test_validate_namespace_uppercase_in_middle():
    """Uppercase letters anywhere should be rejected"""
    validator = validate_namespace(("default",))
    
    test_cases = [
        "com.Example.test",
        "com.exaMple.test",
        "com.example.Test",
        "COM.example.test"
    ]
    
    for test_case in test_cases:
        with pytest.raises(WizardValidationError, match="lower case"):
            validator(test_case)


# Edge case 13: Keywords with different cases (should they be caught?)
@given(st.sampled_from(list(LANGUAGE_KEYWORDS)))
def test_safe_reserved_case_sensitive(keyword):
    """Keywords are case-sensitive - uppercase versions are not keywords"""
    upper_keyword = keyword.upper()
    if upper_keyword != keyword:  # If it has letters that can be uppercased
        result = safe_reserved(upper_keyword)
        # Uppercase version should NOT be treated as keyword
        assert result == upper_keyword
        assert result[-1] != "_"


# Edge case 14: validate_codegen_model edge values
@given(st.sampled_from(["0", "3", "-1", "1.0", "2.0", "01", "02", "10"]))
def test_validate_codegen_model_edge_values(value):
    """Edge values around 1 and 2 should be rejected"""
    validator = validate_codegen_model("1")
    
    with pytest.raises(WizardValidationError, match="Invalid selection"):
        validator(value)


# Edge case 15: Long Java identifiers
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=100, max_size=300))
def test_safe_reserved_long_identifier(long_str):
    """Very long identifiers should still work correctly"""
    result = safe_reserved(long_str)
    # Not a keyword, so unchanged
    assert result == long_str


# Edge case 16: Unicode in namespace
@given(st.text(alphabet="αβγδεζηθικλμνξοπρστυφχψω", min_size=1, max_size=10))
def test_validate_namespace_unicode(unicode_str):
    """Unicode characters should be rejected in namespace"""
    validator = validate_namespace(("default",))
    
    with pytest.raises(WizardValidationError):
        validator(unicode_str)


# Edge case 17: Keywords at boundaries  
def test_safe_reserved_keyword_substrings():
    """Strings containing keywords as substrings should not be modified"""
    # "classy" contains "class" but is not a keyword
    assert safe_reserved("classy") == "classy"
    assert safe_reserved("classic") == "classic"
    assert safe_reserved("subclass") == "subclass"
    
    # "form" is not a keyword even though "for" is
    assert safe_reserved("form") == "form"
    assert safe_reserved("format") == "format"
    
    # But exact match should get underscore
    assert safe_reserved("class") == "class_"
    assert safe_reserved("for") == "for_"