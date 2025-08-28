import sys
import string
sys.path.append('/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from rpdk.java.utils import (
    safe_reserved, 
    safe_reserved_hook_target, 
    LANGUAGE_KEYWORDS,
    HOOK_TARGET_KEYWORDS,
    validate_namespace,
    validate_codegen_model
)
from rpdk.java.resolver import translate_type, PRIMITIVE_TYPES
from rpdk.core.jsonutils.resolver import ResolvedType, ContainerType
from rpdk.core.exceptions import WizardValidationError
import pytest


# Test 1: safe_reserved function properties
@given(st.text(min_size=1, max_size=50))
def test_safe_reserved_idempotence(token):
    """Applying safe_reserved twice should equal applying once (idempotence)"""
    once = safe_reserved(token)
    twice = safe_reserved(safe_reserved(token))
    assert once == twice


@given(st.sampled_from(list(LANGUAGE_KEYWORDS)))
def test_safe_reserved_keywords_get_underscore(keyword):
    """All Java keywords should get an underscore appended"""
    result = safe_reserved(keyword)
    assert result == keyword + "_"
    

@given(st.text(min_size=1, max_size=50).filter(lambda x: x not in LANGUAGE_KEYWORDS))
def test_safe_reserved_non_keywords_unchanged(token):
    """Non-keywords should remain unchanged"""
    result = safe_reserved(token)
    assert result == token


# Test 2: safe_reserved_hook_target function properties
@given(st.sampled_from(list(LANGUAGE_KEYWORDS | HOOK_TARGET_KEYWORDS)))
def test_safe_reserved_hook_target_keywords(keyword):
    """Hook target keywords and language keywords should get underscore"""
    result = safe_reserved_hook_target(keyword)
    assert result == keyword + "_"


@given(st.text(min_size=1, max_size=50).filter(lambda x: x not in (LANGUAGE_KEYWORDS | HOOK_TARGET_KEYWORDS)))
def test_safe_reserved_hook_target_non_keywords(token):
    """Non-keywords should remain unchanged for hook targets"""
    result = safe_reserved_hook_target(token)
    assert result == token


# Test 3: translate_type function properties
@given(st.sampled_from(["string", "integer", "boolean", "number"]))
def test_translate_type_primitives(primitive_type):
    """Primitive types should translate to Java types"""
    resolved = ResolvedType(ContainerType.PRIMITIVE, primitive_type)
    result = translate_type(resolved)
    assert result in ["String", "Integer", "Boolean", "Double", "Long"]
    assert isinstance(result, str)


@given(st.sampled_from(["string", "integer", "boolean", "number"]))
def test_translate_type_list_container(item_type):
    """List containers should produce List<Type> format"""
    inner = ResolvedType(ContainerType.PRIMITIVE, item_type)
    resolved = ResolvedType(ContainerType.LIST, inner)
    result = translate_type(resolved)
    assert result.startswith("List<")
    assert result.endswith(">")


@given(st.sampled_from(["string", "integer", "boolean", "number"]))
def test_translate_type_set_container(item_type):
    """Set containers should produce Set<Type> format"""
    inner = ResolvedType(ContainerType.PRIMITIVE, item_type)
    resolved = ResolvedType(ContainerType.SET, inner)
    result = translate_type(resolved)
    assert result.startswith("Set<")
    assert result.endswith(">")


@given(st.sampled_from(["string", "integer", "boolean", "number"]))
def test_translate_type_dict_container(item_type):
    """Dict containers should produce Map<String, Type> format"""
    inner = ResolvedType(ContainerType.PRIMITIVE, item_type)
    resolved = ResolvedType(ContainerType.DICT, inner)
    result = translate_type(resolved)
    assert result.startswith("Map<String, ")
    assert result.endswith(">")


# Test 4: validate_namespace function properties
@given(st.text(alphabet=string.ascii_lowercase + "_.", min_size=1, max_size=100))
def test_validate_namespace_lowercase_requirement(namespace_str):
    """validate_namespace should reject any uppercase letters"""
    validator = validate_namespace(("default",))
    
    if any(c.isupper() for c in namespace_str):
        with pytest.raises(WizardValidationError, match="lower case"):
            validator(namespace_str)
    elif "." in namespace_str:
        # Check for other validation rules
        segments = namespace_str.split(".")
        should_fail = False
        
        for segment in segments:
            if not segment:
                should_fail = True
                break
            if segment in LANGUAGE_KEYWORDS:
                should_fail = True
                break
            if segment[0] not in string.ascii_lowercase + "_":
                should_fail = True
                break
            # Check pattern match
            import re
            if not re.match(r"^[_a-z][_a-z0-9]+$", segment):
                should_fail = True
                break
        
        if should_fail:
            with pytest.raises(WizardValidationError):
                validator(namespace_str)


@given(st.sampled_from(list(LANGUAGE_KEYWORDS)))
def test_validate_namespace_rejects_keywords(keyword):
    """validate_namespace should reject Java keywords as package segments"""
    validator = validate_namespace(("default",))
    
    # Single keyword
    with pytest.raises(WizardValidationError, match="reserved keyword"):
        validator(keyword)
    
    # Keyword in package path
    with pytest.raises(WizardValidationError, match="reserved keyword"):
        validator(f"com.{keyword}.test")


@given(st.lists(
    st.text(alphabet=string.ascii_lowercase + "_", min_size=2, max_size=20)
    .filter(lambda x: x not in LANGUAGE_KEYWORDS and x[0] in string.ascii_lowercase + "_"),
    min_size=1, max_size=5
))
def test_validate_namespace_valid_packages(segments):
    """Valid package names should be accepted"""
    validator = validate_namespace(("default",))
    namespace_str = ".".join(segments)
    
    # Filter to ensure each segment matches the pattern
    import re
    pattern = r"^[_a-z][_a-z0-9]+$"
    if all(re.match(pattern, seg) for seg in segments):
        result = validator(namespace_str)
        assert result == tuple(segments)


# Test 5: validate_codegen_model function properties
@given(st.text(min_size=1, max_size=10))
def test_validate_codegen_model_only_accepts_1_or_2(value):
    """validate_codegen_model should only accept '1' or '2'"""
    validator = validate_codegen_model("1")
    
    if value in ["1", "2"]:
        result = validator(value)
        assert result == value
    elif value == "":
        result = validator(value)
        assert result == "1"  # default
    else:
        with pytest.raises(WizardValidationError, match="Invalid selection"):
            validator(value)


@given(st.sampled_from(["1", "2"]))
def test_validate_codegen_model_accepts_valid(value):
    """Valid codegen models 1 and 2 should be accepted"""
    validator = validate_codegen_model("1")
    result = validator(value)
    assert result == value


# Test 6: Round-trip property for safe_reserved with unsafe input
@given(st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=1, max_size=50))
def test_safe_reserved_makes_identifier_safe(token):
    """After applying safe_reserved, the result should not be a Java keyword"""
    result = safe_reserved(token)
    # The result should never be a raw keyword (it would have underscore appended)
    assert result not in LANGUAGE_KEYWORDS


# Test 7: Container nesting in translate_type
@given(st.sampled_from(["string", "integer", "boolean", "number"]))
def test_translate_type_nested_list_of_lists(item_type):
    """Nested lists should produce List<List<Type>> format"""
    inner = ResolvedType(ContainerType.PRIMITIVE, item_type)
    list_inner = ResolvedType(ContainerType.LIST, inner)
    resolved = ResolvedType(ContainerType.LIST, list_inner)
    result = translate_type(resolved)
    assert result.startswith("List<List<")
    assert result.endswith(">>")
    assert result.count("<") == result.count(">")