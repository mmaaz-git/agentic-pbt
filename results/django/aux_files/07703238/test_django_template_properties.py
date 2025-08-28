"""Property-based tests for django.template module using Hypothesis."""

import django
from django.conf import settings

# Configure Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test-key-for-hypothesis-testing',
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': False,
        'OPTIONS': {},
    }],
)
django.setup()

from hypothesis import given, strategies as st, assume, settings as hyp_settings
import pytest
from django.template import Template, Context
from django.template.defaultfilters import (
    escape, addslashes, truncatechars, truncatewords,
    upper, lower, capfirst, title, slugify,
    cut, striptags, wordcount
)
from django.utils.html import escape as html_escape
from django.utils.safestring import SafeString, mark_safe


# Strategy for generating text without template syntax
@st.composite
def literal_text(draw):
    """Generate text that doesn't contain Django template syntax."""
    text = draw(st.text(min_size=0, max_size=1000))
    # Filter out template syntax markers
    assume('{%' not in text and '{{' not in text and '%}' not in text and '}}' not in text)
    return text


@given(literal_text())
def test_template_literal_preservation(text):
    """Literal text without template syntax should pass through unchanged."""
    template = Template(text)
    result = template.render(Context())
    assert result == text, f"Template changed literal text: {text!r} -> {result!r}"


@given(st.text(min_size=0, max_size=100))
def test_escape_double_escaping_creates_different_output(text):
    """The escape filter should NOT be idempotent - it double-escapes."""
    once = escape(text)
    twice = escape(once)
    
    # If the text contains escapable characters, double escaping should differ
    if any(c in text for c in '<>&"\''):
        # Double escaping should produce different output
        # This documents the actual behavior - escape is NOT idempotent
        if str(once) != text:  # If first escape changed something
            assert str(twice) != str(once), f"Expected double escape to differ: {text!r}"


@given(st.text(min_size=1, max_size=200), st.integers(min_value=1, max_value=100))
def test_truncatechars_length_invariant(text, max_length):
    """truncatechars should never produce output longer than the specified length."""
    result = truncatechars(text, max_length)
    
    # The result should never be longer than max_length
    assert len(result) <= max_length, (
        f"truncatechars({text!r}, {max_length}) produced {len(result)} chars: {result!r}"
    )
    
    # If text is shorter than max_length, it should be unchanged
    if len(text) <= max_length:
        assert result == text, f"Short text was modified: {text!r} -> {result!r}"


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=100))
def test_upper_lower_roundtrip_ascii(text):
    """For ASCII text, upper(lower(x)) should equal upper(x)."""
    result = upper(lower(text))
    expected = upper(text)
    assert result == expected, f"upper/lower roundtrip failed: {text!r}"


@given(st.text(min_size=0, max_size=100))
def test_addslashes_escapes_quotes_and_backslashes(text):
    """addslashes should escape all quotes and backslashes."""
    result = addslashes(text)
    
    # Count unescaped quotes and backslashes in result
    i = 0
    while i < len(result):
        if result[i] == '\\':
            # Check if this backslash is followed by a quote or another backslash
            if i + 1 < len(result) and result[i + 1] in ['\'', '"', '\\']:
                i += 2  # Skip the escaped character
            else:
                # Unescaped backslash at end or before other character
                assert False, f"Unescaped backslash in addslashes result at position {i}: {result!r}"
        elif result[i] in ['\'', '"']:
            # Check if this quote is escaped
            if i == 0 or result[i - 1] != '\\':
                assert False, f"Unescaped quote '{result[i]}' at position {i}: {result!r}"
        else:
            i += 1


@given(st.text(min_size=0, max_size=100), st.text(min_size=0, max_size=10))
def test_cut_removes_all_occurrences(text, substring):
    """cut filter should remove all occurrences of the substring."""
    assume(substring)  # Skip empty substring
    result = cut(text, substring)
    assert substring not in result, f"cut failed to remove all '{substring}' from {text!r}: {result!r}"


@given(st.text(min_size=0, max_size=500))
def test_wordcount_consistency(text):
    """wordcount should return consistent non-negative integer."""
    count = wordcount(text)
    assert isinstance(count, int), f"wordcount returned non-integer: {type(count)}"
    assert count >= 0, f"wordcount returned negative: {count}"
    
    # Empty string should have 0 words
    if not text or text.isspace():
        assert count == 0, f"Empty/whitespace text has {count} words: {text!r}"
    
    # Text with no spaces should have at most 1 word
    if ' ' not in text and '\t' not in text and '\n' not in text:
        assert count <= 1, f"Text without spaces has {count} words: {text!r}"


@given(st.text(min_size=0, max_size=100))
def test_striptags_removes_all_tags(text):
    """striptags should remove all HTML/XML tags."""
    result = striptags(text)
    
    # Result should not contain any < or > that could form tags
    # Note: striptags should remove entire tags, not just < and >
    tag_start = result.find('<')
    if tag_start != -1:
        tag_end = result.find('>', tag_start)
        if tag_end != -1:
            potential_tag = result[tag_start:tag_end+1]
            # Check if this looks like an HTML tag
            if '/' in potential_tag or any(c.isalpha() for c in potential_tag):
                assert False, f"striptags left potential tag {potential_tag!r} in result: {result!r}"


@given(st.text(min_size=0, max_size=100))
def test_template_empty_context_variables_render_empty(text):
    """Variables not in context should render as empty string."""
    # Create template with a variable reference
    assume('{{' not in text and '}}' not in text)  # Avoid nested template syntax
    template_string = f"{{{{ var_{abs(hash(text)) % 1000000} }}}}"
    template = Template(template_string)
    result = template.render(Context())
    assert result == '', f"Missing variable didn't render as empty: {result!r}"


@given(st.lists(st.text(max_size=20), min_size=0, max_size=10))
def test_template_for_loop_iteration_count(items):
    """For loop should iterate exactly once per item."""
    template = Template('{% for item in items %}X{% endfor %}')
    context = Context({'items': items})
    result = template.render(context)
    assert result == 'X' * len(items), f"For loop produced {result!r} for {len(items)} items"


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=50))
def test_slugify_produces_valid_slug(text):
    """slugify should produce a valid URL slug according to Django's documentation."""
    result = slugify(text)
    
    # Per Django docs: should only contain alphanumerics, underscores, or hyphens
    for char in result:
        assert char.isalnum() or char in '-_', f"Invalid character '{char}' in slug: {result!r}"
    
    # Result should not start or end with hyphen or underscore
    if result:
        assert not result.startswith('-'), f"Slug starts with hyphen: {result!r}"
        assert not result.endswith('-'), f"Slug ends with hyphen: {result!r}"
        assert not result.startswith('_'), f"Slug starts with underscore: {result!r}"
        assert not result.endswith('_'), f"Slug ends with underscore: {result!r}"
    
    # No consecutive hyphens
    assert '--' not in result, f"Consecutive hyphens in slug: {result!r}"


@given(st.integers(min_value=0, max_value=1000), st.integers(min_value=1, max_value=100))
def test_truncatewords_word_count(num_words, max_words):
    """truncatewords should respect the word limit."""
    # Generate text with known number of words
    text = ' '.join(['word'] * num_words)
    result = truncatewords(text, max_words)
    
    # Count words in result (excluding both types of ellipsis)
    result_text = result.replace('...', '').replace('…', '').strip()
    if result_text:
        result_words = len(result_text.split())
    else:
        result_words = 0
    
    expected_words = min(num_words, max_words)
    assert result_words <= expected_words, (
        f"truncatewords produced {result_words} words, expected <= {expected_words}"
    )


if __name__ == '__main__':
    # Run with increased examples for better coverage
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])