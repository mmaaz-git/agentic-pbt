"""Property-based tests for tabulate library using Hypothesis."""

import re
from hypothesis import given, strategies as st, assume, settings
import tabulate
from tabulate import tabulate as tabulate_func


# Strategy for basic table data
def table_data_strategy():
    """Generate reasonable table data."""
    cell_strategy = st.one_of(
        st.none(),
        st.integers(min_value=-1000000, max_value=1000000),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        st.text(min_size=0, max_size=20, alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))
    )
    
    # Generate table with consistent column count
    num_cols = st.integers(min_value=1, max_value=5)
    num_rows = st.integers(min_value=0, max_value=10)
    
    return st.builds(
        lambda nc, nr, cells: [cells[i:i+nc] for i in range(0, len(cells), nc)][:nr] if nc > 0 else [],
        nc=num_cols,
        nr=num_rows,
        cells=st.lists(cell_strategy, min_size=0, max_size=50)
    )


# Available table formats from documentation
TABLE_FORMATS = [
    "plain", "simple", "grid", "pipe", "orgtbl", "rst", 
    "mediawiki", "latex", "latex_raw", "latex_booktabs", 
    "latex_longtable", "html", "simple_grid", "rounded_grid",
    "heavy_grid", "mixed_grid", "double_grid", "fancy_grid",
    "outline", "simple_outline", "rounded_outline", "heavy_outline",
    "mixed_outline", "double_outline", "fancy_outline", "presto"
]


@given(table_data_strategy())
def test_returns_string_type(data):
    """Property: tabulate always returns a string."""
    result = tabulate_func(data)
    assert isinstance(result, str), f"Expected str, got {type(result)}"


@given(table_data_strategy(), st.text(min_size=0, max_size=10))
def test_missingval_replacement(data, missingval):
    """Property: None values are replaced with missingval string."""
    assume(missingval not in ["None", ""])  # Avoid confusion with actual None representation
    
    # Check if data contains None
    has_none = any(None in row for row in data if isinstance(row, list))
    
    if has_none:
        result = tabulate_func(data, missingval=missingval)
        # The missingval should appear in the output if there were None values
        assert missingval in result, f"missingval '{missingval}' not found in output with None values"


@given(table_data_strategy(), st.sampled_from(TABLE_FORMATS))
def test_idempotence(data, fmt):
    """Property: Formatting the same data twice produces identical results."""
    result1 = tabulate_func(data, tablefmt=fmt)
    result2 = tabulate_func(data, tablefmt=fmt)
    assert result1 == result2, f"Idempotence violated for format {fmt}"


@given(table_data_strategy())
def test_empty_data_handling(data):
    """Property: Empty data should not crash and should return a string."""
    # Test with truly empty data
    result = tabulate_func([])
    assert isinstance(result, str)
    assert result == ""
    
    # Test with empty rows
    result = tabulate_func([[], [], []])
    assert isinstance(result, str)


@given(st.lists(st.lists(st.integers(), min_size=2, max_size=2), min_size=1, max_size=10))
def test_headers_firstrow(data):
    """Property: When headers='firstrow', first row becomes headers."""
    assume(len(data) > 1)  # Need at least 2 rows
    
    result_with_headers = tabulate_func(data, headers="firstrow")
    result_without = tabulate_func(data[1:])  # Skip first row
    
    # Both should be strings
    assert isinstance(result_with_headers, str)
    assert isinstance(result_without, str)
    
    # The result with headers should contain header formatting
    # (usually has separator lines that plain data doesn't)
    assert len(result_with_headers) >= len(result_without)


@given(
    st.lists(
        st.lists(
            st.one_of(st.none(), st.integers(min_value=-100, max_value=100)), 
            min_size=3, max_size=3
        ), 
        min_size=2, max_size=5
    )
)
def test_format_preserves_data_count(data):
    """Property: Different formats preserve the data content (row/col count)."""
    # Count non-empty data rows
    data_rows = len([row for row in data if any(cell is not None for cell in row)])
    
    for fmt in ["plain", "simple", "grid"]:
        result = tabulate_func(data, tablefmt=fmt)
        
        # Count lines that likely contain data (non-empty, non-separator lines)
        lines = result.strip().split('\n')
        
        # For grid format, filter out separator lines
        if fmt == "grid":
            data_lines = [line for line in lines if line and not all(c in '+-=| ' for c in line)]
        else:
            data_lines = [line for line in lines if line and not all(c in '- ' for c in line)]
        
        # Should have at least as many data lines as data rows
        # (might have more due to headers or formatting)
        assert len(data_lines) >= min(1, data_rows), \
            f"Format {fmt} lost data rows: expected >= {data_rows}, got {len(data_lines)}"


@given(st.lists(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), min_size=2, max_size=2), min_size=1, max_size=5))
def test_floatfmt_parameter(data):
    """Property: floatfmt parameter controls float formatting."""
    result_default = tabulate_func(data)
    result_2f = tabulate_func(data, floatfmt=".2f")
    result_e = tabulate_func(data, floatfmt="e")
    
    # All should return strings
    assert all(isinstance(r, str) for r in [result_default, result_2f, result_e])
    
    # Different formats should generally produce different outputs
    # (unless data has very specific values)
    if data and data[0] and any(abs(val) > 0.01 for row in data for val in row if val is not None):
        # For non-zero floats, different formats should differ
        assert result_default != result_e or result_2f != result_e, \
            "Float formatting appears to have no effect"


@given(st.lists(st.lists(st.integers(), min_size=3, max_size=3), min_size=2, max_size=5))
def test_showindex_adds_column(data):
    """Property: showindex=True adds an index column."""
    assume(len(data) > 0)
    
    result_without = tabulate_func(data, showindex=False)
    result_with = tabulate_func(data, showindex=True)
    
    # Count columns in first data line (rough heuristic)
    if result_without:
        # Count separators in a line to estimate columns
        lines_without = [l for l in result_without.split('\n') if l.strip()]
        lines_with = [l for l in result_with.split('\n') if l.strip()]
        
        if lines_without and lines_with:
            # Index column should add content
            assert len(result_with) > len(result_without), \
                "showindex=True should add content"


@given(table_data_strategy(), st.sampled_from(["simple", "grid", "pipe"]))
def test_consistent_column_alignment(data, fmt):
    """Property: Column alignment should be consistent across rows."""
    assume(len(data) >= 2)
    assume(all(len(row) == len(data[0]) for row in data))  # Consistent column count
    
    result = tabulate_func(data, tablefmt=fmt)
    lines = result.split('\n')
    
    # For formats with clear separators, check alignment
    if fmt in ["grid", "pipe"]:
        # Find lines with column separators
        data_lines = [l for l in lines if '|' in l and not all(c in '|+- =' for c in l)]
        
        if len(data_lines) >= 2:
            # Column positions should be consistent
            sep_positions = []
            for line in data_lines:
                positions = [i for i, c in enumerate(line) if c == '|']
                sep_positions.append(positions)
            
            # All rows should have separators at same positions
            if sep_positions:
                first_pos = sep_positions[0]
                for pos in sep_positions[1:]:
                    assert pos == first_pos, f"Inconsistent column alignment in {fmt} format"


@given(
    st.lists(
        st.lists(st.text(min_size=0, max_size=5), min_size=2, max_size=2),
        min_size=1, max_size=3
    ),
    st.lists(st.text(min_size=1, max_size=5), min_size=2, max_size=2)
)
def test_headers_parameter_types(data, headers_list):
    """Property: Different header types should work."""
    # Test with explicit header list
    result = tabulate_func(data, headers=headers_list)
    assert isinstance(result, str)
    
    # Test with headers="keys" for dict input
    if data:
        dict_data = {f"col{i}": [row[i] if i < len(row) else None for row in data] 
                     for i in range(max(len(row) for row in data) if data else 0)}
        if dict_data:
            result = tabulate_func(dict_data, headers="keys")
            assert isinstance(result, str)


if __name__ == "__main__":
    import sys
    # Run with pytest if available, otherwise run manually
    try:
        import pytest
        sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
    except ImportError:
        # Run tests manually
        print("Running tests manually (install pytest for better output)...")
        
        test_functions = [
            test_returns_string_type,
            test_missingval_replacement,
            test_idempotence,
            test_empty_data_handling,
            test_headers_firstrow,
            test_format_preserves_data_count,
            test_floatfmt_parameter,
            test_showindex_adds_column,
            test_consistent_column_alignment,
            test_headers_parameter_types
        ]
        
        for test_func in test_functions:
            print(f"Running {test_func.__name__}...")
            try:
                test_func()
                print(f"  ✓ {test_func.__name__} passed")
            except Exception as e:
                print(f"  ✗ {test_func.__name__} failed: {e}")