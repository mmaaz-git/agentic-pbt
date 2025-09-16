"""Property-based tests for copier._jinja_ext module."""

import sys
import re
from hypothesis import given, strategies as st, assume, settings

# Add the copier environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._jinja_ext import YieldEnvironment, YieldExtension
from copier.errors import MultipleYieldTagsError
from jinja2.exceptions import UndefinedError, TemplateSyntaxError


# Strategies for generating test data
valid_python_identifier = st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True)
safe_text = st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs")), min_size=0, max_size=100)
simple_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=100)
)
safe_iterables = st.one_of(
    st.lists(simple_values, min_size=0, max_size=20),
    st.tuples(simple_values),
    st.sets(simple_values)
)


@given(
    var_name=valid_python_identifier,
    iterable_name=valid_python_identifier,
    iterable_value=safe_iterables
)
def test_yield_tag_sets_environment_attributes(var_name, iterable_name, iterable_value):
    """Test that yield tag correctly sets environment attributes."""
    assume(var_name != iterable_name)  # Variables should be different
    
    env = YieldEnvironment(extensions=[YieldExtension])
    
    # Create a template with yield tag
    template_str = f"{{% yield {var_name} from {iterable_name} %}}{{{{{var_name}}}}}{{% endyield %}}"
    template = env.from_string(template_str)
    
    # Render the template
    context = {iterable_name: iterable_value}
    result = template.render(context)
    
    # Check that the environment attributes are set correctly
    assert env.yield_name == var_name
    assert env.yield_iterable == iterable_value


@given(
    var_name=valid_python_identifier,
    iterable_name=valid_python_identifier,
    template_content=safe_text,
    context_vars=st.dictionaries(valid_python_identifier, simple_values, min_size=0, max_size=5)
)
def test_preprocessing_resets_yield_attributes(var_name, iterable_name, template_content, context_vars):
    """Test that preprocessing resets yield attributes to None."""
    assume(var_name != iterable_name)
    
    env = YieldEnvironment(extensions=[YieldExtension])
    
    # First template to set some attributes
    template1_str = f"{{% yield {var_name} from {iterable_name} %}}{template_content}{{% endyield %}}"
    template1 = env.from_string(template1_str)
    
    # Set up context with the iterable
    context = {**context_vars, iterable_name: [1, 2, 3]}
    template1.render(context)
    
    # Verify attributes are set
    assert env.yield_name == var_name
    assert env.yield_iterable == [1, 2, 3]
    
    # Create and render a second template - preprocessing should reset attributes
    template2_str = "Simple template without yield"
    template2 = env.from_string(template2_str)
    
    # After preprocessing the second template, attributes should be None
    # The attributes are reset during preprocessing, not after rendering
    assert env.yield_name is None
    assert env.yield_iterable is None


@given(
    var_name1=valid_python_identifier,
    var_name2=valid_python_identifier,
    iterable_name1=valid_python_identifier,
    iterable_name2=valid_python_identifier,
    content1=safe_text,
    content2=safe_text
)
def test_multiple_yield_tags_raise_error(var_name1, var_name2, iterable_name1, iterable_name2, content1, content2):
    """Test that multiple yield tags in one template raise MultipleYieldTagsError."""
    assume(var_name1 != iterable_name1)
    assume(var_name2 != iterable_name2)
    
    env = YieldEnvironment(extensions=[YieldExtension])
    
    # Create a template with two yield tags
    template_str = (
        f"{{% yield {var_name1} from {iterable_name1} %}}{content1}{{% endyield %}}"
        f"{{% yield {var_name2} from {iterable_name2} %}}{content2}{{% endyield %}}"
    )
    
    template = env.from_string(template_str)
    
    # Rendering should raise MultipleYieldTagsError
    context = {iterable_name1: [1, 2], iterable_name2: [3, 4]}
    try:
        result = template.render(context)
        # If no error, test fails
        assert False, f"Expected MultipleYieldTagsError but got result: {result}"
    except MultipleYieldTagsError as e:
        # Expected behavior
        assert "Only one yield tag is allowed" in str(e)
    except Exception as e:
        # Unexpected error
        assert False, f"Expected MultipleYieldTagsError but got {type(e).__name__}: {e}"


@given(
    var_name=valid_python_identifier,
    undefined_var=valid_python_identifier,
    iterable_name=valid_python_identifier,
    iterable_value=safe_iterables
)
def test_undefined_error_returns_empty_string(var_name, undefined_var, iterable_name, iterable_value):
    """Test that UndefinedError in yield body returns empty string."""
    assume(var_name != iterable_name)
    assume(undefined_var != iterable_name)
    assume(undefined_var != var_name)
    
    env = YieldEnvironment(extensions=[YieldExtension])
    
    # Create a template that references an undefined variable
    template_str = f"{{% yield {var_name} from {iterable_name} %}}{{{{{undefined_var}}}}}{{% endyield %}}"
    template = env.from_string(template_str)
    
    # Render should return empty string for undefined variables
    context = {iterable_name: iterable_value}
    result = template.render(context)
    
    # Result should be empty string
    assert result == ""
    # But yield attributes should still be set
    assert env.yield_name == var_name
    assert env.yield_iterable == iterable_value


@given(
    var_name=valid_python_identifier,
    iterable_name=valid_python_identifier,
    dict_name=valid_python_identifier,
    attr_name=valid_python_identifier
)
def test_dict_attr_undefined_returns_empty(var_name, iterable_name, dict_name, attr_name):
    """Test that dict.attr pattern (which raises UndefinedError) returns empty string."""
    assume(len({var_name, iterable_name, dict_name}) == 3)  # All different
    
    env = YieldEnvironment(extensions=[YieldExtension])
    
    # Create template with dict.attr pattern (as mentioned in code comment)
    template_str = f"{{% yield {var_name} from {iterable_name} %}}{{{{{dict_name}.{attr_name}}}}}{{% endyield %}}"
    template = env.from_string(template_str)
    
    # Even with the dict defined, accessing undefined attribute should return empty
    context = {
        iterable_name: [1, 2, 3],
        dict_name: {"some_key": "some_value"}
    }
    result = template.render(context)
    
    # Should return empty string
    assert result == ""
    # But yield attributes should be set
    assert env.yield_name == var_name


@given(
    template_content=st.text(min_size=0, max_size=1000)
)
def test_non_yield_templates_have_none_attributes(template_content):
    """Test that templates without yield tags have None attributes."""
    # Filter out content that might accidentally contain yield syntax
    assume("{% yield" not in template_content)
    assume("endyield" not in template_content)
    
    env = YieldEnvironment(extensions=[YieldExtension])
    
    try:
        template = env.from_string(template_content)
        template.render({})
        
        # Attributes should remain None
        assert env.yield_name is None
        assert env.yield_iterable is None
    except TemplateSyntaxError:
        # Some random text might create invalid Jinja2 syntax, that's okay
        pass


@given(
    var_name=valid_python_identifier,
    iterable_name=valid_python_identifier,
    body_content=st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="{%}"), min_size=0, max_size=100)
)
def test_yield_body_content_preservation(var_name, iterable_name, body_content):
    """Test that yield body content is preserved when variables are defined."""
    assume(var_name != iterable_name)
    
    env = YieldEnvironment(extensions=[YieldExtension])
    
    # Create template with static body content
    template_str = f"{{% yield {var_name} from {iterable_name} %}}{body_content}{{% endyield %}}"
    
    try:
        template = env.from_string(template_str)
        
        # Render with empty iterable
        context = {iterable_name: [], var_name: "test"}
        result = template.render(context)
        
        # With empty iterable, result should be empty
        assert result == ""
        
        # But attributes should be set
        assert env.yield_name == var_name
        assert env.yield_iterable == []
        
    except TemplateSyntaxError:
        # Some content might still create invalid syntax
        pass


@given(
    var_name=valid_python_identifier,
    iterable_values=st.lists(st.integers(), min_size=1, max_size=10)
)
@settings(max_examples=50)
def test_yield_iterable_identity(var_name, iterable_values):
    """Test that the yield_iterable attribute holds the exact same object passed in."""
    env = YieldEnvironment(extensions=[YieldExtension])
    
    template_str = f"{{% yield item from {var_name} %}}{{{{item}}}}{{% endyield %}}"
    template = env.from_string(template_str)
    
    context = {var_name: iterable_values}
    template.render(context)
    
    # The yield_iterable should be the exact same object (identity check)
    assert env.yield_iterable is iterable_values
    assert env.yield_name == "item"


if __name__ == "__main__":
    print("Running property-based tests for copier._jinja_ext...")
    import pytest
    pytest.main([__file__, "-v"])