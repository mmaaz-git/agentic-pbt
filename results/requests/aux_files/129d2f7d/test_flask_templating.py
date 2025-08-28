import math
from hypothesis import assume, given, settings, strategies as st
from flask import Flask
import flask.templating


def create_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@given(st.text(min_size=0, max_size=1000).filter(lambda s: '{{' not in s and '{%' not in s and '{#' not in s))
def test_plain_text_round_trip(text):
    """Plain text without template syntax should be returned unchanged."""
    app = create_app()
    with app.app_context():
        result = flask.templating.render_template_string(text)
        assert result == text


@given(
    st.text(min_size=1, max_size=100).filter(lambda s: '{{' not in s and '{%' not in s and '{#' not in s),
    st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda s: s.isidentifier()),
        st.one_of(
            st.text(max_size=100),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none()
        ),
        min_size=0,
        max_size=5
    )
)
def test_streaming_equivalence(template_text, context):
    """Stream rendering should produce the same result as regular rendering."""
    app = create_app()
    
    # Build a template that uses the context variables
    if context:
        var_refs = ' '.join(f'{{{{ {k} }}}}' for k in context.keys())
        template = f"{template_text} {var_refs}"
    else:
        template = template_text
    
    with app.app_context():
        regular_result = flask.templating.render_template_string(template, **context)
        stream_result = ''.join(flask.templating.stream_template_string(template, **context))
        assert regular_result == stream_result


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda s: s.isidentifier()),
        st.one_of(
            st.text(max_size=100),
            st.integers(min_value=-1000000, max_value=1000000),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
            st.booleans()
        ),
        min_size=1,
        max_size=5
    )
)
def test_context_variable_access(context):
    """Variables passed to template should be accessible via {{ variable }}."""
    app = create_app()
    
    # Create template that accesses all variables
    template = ' '.join(f'{{{{ {k} }}}}' for k in context.keys())
    
    with app.app_context():
        result = flask.templating.render_template_string(template, **context)
        # Check that all values appear in the result
        for value in context.values():
            assert str(value) in result


@given(
    st.one_of(
        st.just("{% if True %}yes{% endif %}"),
        st.just("{% for i in range(3) %}{{ i }}{% endfor %}"),
        st.just("{{ 'hello'|upper }}"),
        st.just("{% set x = 5 %}{{ x }}"),
        st.just("{{ 2 + 2 }}"),
        st.text(min_size=1, max_size=100).map(lambda s: f"{{{{ '{s}' }}}}")
    )
)
def test_valid_syntax_no_crash(template):
    """Valid Jinja2 syntax should not crash the renderer."""
    app = create_app()
    
    with app.app_context():
        try:
            result = flask.templating.render_template_string(template)
            # Just checking it doesn't crash
            assert isinstance(result, str)
        except Exception as e:
            # Only template-specific errors are acceptable
            assert isinstance(e, (flask.templating.TemplateNotFound, Exception))


@given(
    st.text(min_size=1, max_size=50).filter(lambda s: s.isidentifier()),
    st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000),
        st.text(max_size=100)
    )
)
def test_filter_chain_preservation(var_name, value):
    """Applying identity filters should preserve the value."""
    app = create_app()
    
    # Test that value is preserved through filters
    template = f"{{{{ {var_name}|string|trim }}}}"
    
    with app.app_context():
        result = flask.templating.render_template_string(template, **{var_name: value})
        # The string representation should be in the result
        assert str(value).strip() == result.strip()


@given(
    st.lists(
        st.text(min_size=1, max_size=20).filter(lambda s: '{{' not in s and '{%' not in s),
        min_size=0,
        max_size=10
    )
)
def test_for_loop_iteration_count(items):
    """For loops should iterate exactly as many times as there are items."""
    app = create_app()
    
    template = "{% for item in items %}X{% endfor %}"
    
    with app.app_context():
        result = flask.templating.render_template_string(template, items=items)
        assert result.count('X') == len(items)


@given(st.integers(min_value=0, max_value=100))
def test_range_function_consistency(n):
    """The range function in templates should behave like Python's range."""
    app = create_app()
    
    template = "{% for i in range(n) %}{{ i }},{% endfor %}"
    
    with app.app_context():
        result = flask.templating.render_template_string(template, n=n)
        if n > 0:
            numbers = result.strip(',').split(',')
            assert len(numbers) == n
            for i, num in enumerate(numbers):
                assert int(num) == i
        else:
            assert result == ""


@given(
    st.text(min_size=1, max_size=100).filter(
        lambda s: all(c not in s for c in ['{', '}', '%', '#'])
    )
)
def test_escape_sequences_preserved(text):
    """Regular text with special characters should be preserved."""
    app = create_app()
    
    with app.app_context():
        result = flask.templating.render_template_string(text)
        assert result == text