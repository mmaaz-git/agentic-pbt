import random
import string
from datetime import datetime

from hypothesis import assume, given, settings, strategies as st
import click.formatting


@given(st.lists(st.tuples(st.text(), st.text()), min_size=1))
def test_measure_table_returns_correct_count(rows):
    widths = click.formatting.measure_table(rows)
    max_col_count = max(len(row) for row in rows)
    assert len(widths) == max_col_count


@given(st.lists(st.tuples(st.text(), st.text()), min_size=1))
def test_measure_table_widths_are_maximums(rows):
    from click._compat import term_len
    widths = click.formatting.measure_table(rows)
    
    for row_idx, row in enumerate(rows):
        for col_idx, col in enumerate(row):
            col_len = term_len(col)
            assert widths[col_idx] >= col_len, f"Width {widths[col_idx]} < {col_len} for column {col_idx}"


@given(
    st.lists(st.tuples(st.text(), st.text()), min_size=1),
    st.integers(min_value=1, max_value=10)
)
def test_iter_rows_consistent_length(rows, col_count):
    result = list(click.formatting.iter_rows(rows, col_count))
    
    for row in result:
        assert len(row) == col_count
    
    assert len(result) == len(rows)


@given(
    st.lists(st.tuples(st.text(min_size=1), st.text()), min_size=1),
    st.integers(min_value=2, max_value=5)
)
def test_iter_rows_preserves_content(rows, col_count):
    result = list(click.formatting.iter_rows(rows, col_count))
    
    for idx, (original, padded) in enumerate(zip(rows, result)):
        for col_idx, col in enumerate(original):
            assert padded[col_idx] == col
        
        for pad_idx in range(len(original), col_count):
            assert padded[pad_idx] == ""


@given(
    st.text(min_size=1).filter(lambda x: '\x08' not in x and '\x00' not in x),
    st.integers(min_value=10, max_value=100),
    st.text(max_size=20).filter(lambda x: '\x08' not in x and '\x00' not in x),
    st.text(max_size=20).filter(lambda x: '\x08' not in x and '\x00' not in x)
)
def test_wrap_text_preserves_non_whitespace(text, width, initial_indent, subsequent_indent):
    wrapped = click.formatting.wrap_text(
        text, 
        width=width,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
        preserve_paragraphs=False
    )
    
    original_non_ws = ''.join(text.split())
    wrapped_without_indents = wrapped.replace(initial_indent, '', 1)
    wrapped_without_indents = wrapped_without_indents.replace(subsequent_indent, '')
    wrapped_non_ws = ''.join(wrapped_without_indents.split())
    
    assert original_non_ws == wrapped_non_ws


@given(
    st.text(min_size=1).filter(lambda x: '\x08' not in x and '\x00' not in x),
    st.integers(min_value=20, max_value=200)
)
def test_wrap_text_respects_width(text, width):
    wrapped = click.formatting.wrap_text(text, width=width)
    
    lines = wrapped.splitlines()
    for line in lines:
        from click._compat import term_len
        assert term_len(line) <= width, f"Line '{line}' has length {term_len(line)} > {width}"


@given(st.lists(st.text(min_size=1).filter(lambda x: '/' not in x and '-' in x), min_size=1, max_size=10))
def test_join_options_preserves_all_options(options):
    joined, has_slash = click.formatting.join_options(options)
    
    for opt in options:
        assert opt in joined
    
    assert not has_slash


@given(st.lists(st.one_of(
    st.text(min_size=2).map(lambda x: f"/{x}"),
    st.text(min_size=2).map(lambda x: f"-{x}"),
    st.text(min_size=2).map(lambda x: f"--{x}")
), min_size=1, max_size=10))
def test_join_options_detects_slash(options):
    joined, has_slash = click.formatting.join_options(options)
    
    expected_slash = any(opt.startswith('/') for opt in options)
    assert has_slash == expected_slash


@given(st.integers(min_value=0, max_value=20), st.integers(min_value=1, max_value=10))
def test_help_formatter_indent_dedent_inverse(initial_indent, increment):
    formatter = click.formatting.HelpFormatter(indent_increment=increment)
    formatter.current_indent = initial_indent
    
    formatter.indent()
    assert formatter.current_indent == initial_indent + increment
    
    formatter.dedent()
    assert formatter.current_indent == initial_indent


@given(st.text())
def test_help_formatter_write_getvalue_roundtrip(text):
    formatter = click.formatting.HelpFormatter()
    formatter.write(text)
    assert formatter.getvalue() == text


@given(st.lists(st.text(), min_size=1))
def test_help_formatter_multiple_writes_concatenate(texts):
    formatter = click.formatting.HelpFormatter()
    for text in texts:
        formatter.write(text)
    assert formatter.getvalue() == ''.join(texts)


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=30).filter(lambda x: '\n' not in x),
            st.text(min_size=0, max_size=100).filter(lambda x: '\n' not in x)
        ),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100)
def test_help_formatter_write_dl_basic(rows):
    formatter = click.formatting.HelpFormatter(width=80)
    
    try:
        formatter.write_dl(rows)
        output = formatter.getvalue()
        
        for term, _ in rows:
            assert term in output
        
    except Exception as e:
        if "Expected two columns" in str(e):
            assume(False)
        else:
            raise


@given(st.integers(min_value=30, max_value=200))
def test_help_formatter_width_property(width):
    formatter = click.formatting.HelpFormatter(width=width)
    assert formatter.width == width


@given(
    st.text(min_size=1, max_size=50).filter(lambda x: '\x00' not in x),
    st.text(min_size=0, max_size=50).filter(lambda x: '\x00' not in x)
)
def test_help_formatter_write_usage_contains_prog(prog, args):
    formatter = click.formatting.HelpFormatter(width=80)
    formatter.write_usage(prog, args)
    output = formatter.getvalue()
    assert prog in output


@given(st.text(min_size=1).filter(lambda x: '\x00' not in x and '\n' not in x))
def test_help_formatter_write_heading_contains_heading(heading):
    formatter = click.formatting.HelpFormatter()
    formatter.write_heading(heading)
    output = formatter.getvalue()
    assert heading in output
    assert output.endswith(":\n")


@given(
    st.integers(min_value=2, max_value=10),
    st.integers(min_value=50, max_value=200)
)
def test_help_formatter_context_managers(indent_increment, width):
    formatter = click.formatting.HelpFormatter(
        indent_increment=indent_increment,
        width=width
    )
    
    initial = formatter.current_indent
    
    with formatter.indentation():
        assert formatter.current_indent == initial + indent_increment
        
        with formatter.indentation():
            assert formatter.current_indent == initial + 2 * indent_increment
        
        assert formatter.current_indent == initial + indent_increment
    
    assert formatter.current_indent == initial


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])