import click.formatting
from hypothesis import given, strategies as st


# Bug 1: iter_rows doesn't truncate when col_count < row length
@given(
    st.lists(
        st.tuples(st.text(min_size=1), st.text(), st.text()),
        min_size=1,
        max_size=5
    )
)
def test_iter_rows_should_truncate_to_col_count(rows):
    # When col_count is less than actual columns, should truncate
    col_count = 2  # Request 2 columns but rows have 3
    result = list(click.formatting.iter_rows(rows, col_count))
    
    for row in result:
        assert len(row) == col_count, f"Expected {col_count} columns, got {len(row)}"


# Bug 2: write_usage loses program name when args is empty
@given(st.text(min_size=1, max_size=20).filter(lambda x: '\x00' not in x and '\n' not in x))
def test_write_usage_with_empty_args_loses_prog(prog):
    formatter = click.formatting.HelpFormatter(width=80)
    formatter.write_usage(prog, '')  # Empty args
    output = formatter.getvalue()
    
    # The program name should appear in the output
    assert prog in output, f"Program name '{prog}' not in output: {repr(output)}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])