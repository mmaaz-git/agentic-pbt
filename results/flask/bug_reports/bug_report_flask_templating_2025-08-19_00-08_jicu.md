# Bug Report: flask.templating Reserved Word Variable Shadowing

**Target**: `flask.templating.render_template_string` and `flask.templating.stream_template_string`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Context variables with names matching Jinja2 reserved words (true, false, none, True, False, None) are inaccessible in templates, as the reserved word literals take precedence over the context variables.

## Property-Based Test

```python
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
    
    template = f"{{ {var_name}|string|trim }}"
    
    with app.app_context():
        result = flask.templating.render_template_string(template, **{var_name: value})
        assert str(value).strip() == result.strip()
```

**Failing input**: `var_name='false', value=0`

## Reproducing the Bug

```python
from flask import Flask
import flask.templating

app = Flask(__name__)

with app.app_context():
    template = '{{ false }}'
    result = flask.templating.render_template_string(template, false=42)
    print(f'Template: {template}')
    print(f'Context: false=42')
    print(f'Expected: 42')
    print(f'Actual: {result}')
    assert result == '42', f"Expected '42' but got '{result}'"
```

## Why This Is A Bug

This violates the fundamental expectation that context variables passed to a template should be accessible within that template. Users who pass data with keys like 'true', 'false', or 'none' will silently get the wrong values (boolean/null literals instead of their data). This is particularly problematic when:

1. Processing user-generated data where field names aren't controlled
2. Working with external APIs that use these as field names
3. Migrating from other templating systems where this works

The behavior is undocumented and breaks the principle of least surprise. Context variables should take precedence over language literals, or at minimum, this limitation should be clearly documented.

## Fix

This is a Jinja2 behavior inherited by Flask. A proper fix would require changes at the Jinja2 level to prioritize context variables over reserved words. As a workaround, Flask could:

1. Document this limitation clearly in the Flask templating documentation
2. Optionally warn users when context contains reserved word keys
3. Provide a template filter to explicitly access shadowed variables

Example warning implementation:
```diff
def render_template_string(source: str, **context: t.Any) -> str:
+   reserved_words = {'true', 'false', 'none', 'True', 'False', 'None'}
+   shadowed = reserved_words & set(context.keys())
+   if shadowed:
+       import warnings
+       warnings.warn(f"Context variables {shadowed} shadow Jinja2 reserved words and will be inaccessible", UserWarning)
    app = current_app._get_current_object()
    template = app.jinja_env.from_string(source)
    return _render(app, template, context)
```