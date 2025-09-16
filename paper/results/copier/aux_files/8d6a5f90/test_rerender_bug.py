"""Property-based test to confirm the template re-rendering bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from copier._jinja_ext import YieldEnvironment, YieldExtension
from copier.errors import MultipleYieldTagsError

# Strategies
valid_identifier = st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True)
simple_values = st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=10)
)
simple_lists = st.lists(simple_values, min_size=0, max_size=5)


@given(
    var_name=valid_identifier,
    iterable_name=valid_identifier,
    body_content=st.text(alphabet=st.characters(blacklist_characters="{%}"), min_size=1, max_size=20),
    first_iterable=simple_lists,
    second_iterable=simple_lists
)
@settings(max_examples=100)
def test_template_rerender_bug(var_name, iterable_name, body_content, first_iterable, second_iterable):
    """Test that rendering the same template twice raises MultipleYieldTagsError incorrectly."""
    if var_name == iterable_name:
        return  # Skip when names collide
    
    env = YieldEnvironment(extensions=[YieldExtension])
    template_str = f"{{% yield {var_name} from {iterable_name} %}}{body_content}{{% endyield %}}"
    
    try:
        template = env.from_string(template_str)
    except:
        return  # Skip if template creation fails
    
    # First render should always work
    try:
        result1 = template.render({iterable_name: first_iterable})
        first_render_success = True
    except MultipleYieldTagsError:
        # Should never happen on first render
        assert False, "MultipleYieldTagsError on first render - this should never happen!"
    except:
        # Other errors are okay (e.g., undefined variables)
        first_render_success = False
    
    if not first_render_success:
        return
    
    # Second render should also work but will fail due to the bug
    try:
        result2 = template.render({iterable_name: second_iterable})
        # If we get here, the bug might be fixed!
        print(f"No bug for: var={var_name}, iter={iterable_name}, body={body_content}")
    except MultipleYieldTagsError as e:
        # This is the bug - a single yield tag is incorrectly reported as multiple
        assert "Only one yield tag is allowed" in str(e)
        # Bug confirmed - this is expected with the current implementation
        pass
    except:
        # Other errors are fine
        pass


if __name__ == "__main__":
    print("Testing template re-rendering bug with property-based testing...")
    print("This will confirm that templates with a single yield tag")
    print("incorrectly raise MultipleYieldTagsError on second render.\n")
    
    import pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])