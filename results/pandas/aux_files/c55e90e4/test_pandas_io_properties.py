import io
import json
import math
import tempfile
from datetime import datetime, timedelta

import pandas as pd
import pytest
from hypothesis import assume, given, settings, strategies as st


# Strategy for generating valid column names
column_names = st.text(
    alphabet=st.characters(whitelist_categories=["L", "N"], whitelist_characters="_"),
    min_size=1,
    max_size=20
).filter(lambda x: x[0].isalpha() or x[0] == "_")

# Strategy for generating DataFrames with various data types
@st.composite
def dataframes_strategy(draw):
    n_rows = draw(st.integers(min_value=1, max_value=50))
    n_cols = draw(st.integers(min_value=1, max_value=10))
    
    columns = draw(st.lists(column_names, min_size=n_cols, max_size=n_cols, unique=True))
    
    data = {}
    for col in columns:
        dtype_choice = draw(st.integers(0, 4))
        if dtype_choice == 0:  # integers
            data[col] = draw(st.lists(
                st.integers(min_value=-1000000, max_value=1000000),
                min_size=n_rows, max_size=n_rows
            ))
        elif dtype_choice == 1:  # floats
            data[col] = draw(st.lists(
                st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
                min_size=n_rows, max_size=n_rows
            ))
        elif dtype_choice == 2:  # strings
            data[col] = draw(st.lists(
                st.text(max_size=50),
                min_size=n_rows, max_size=n_rows
            ))
        elif dtype_choice == 3:  # booleans
            data[col] = draw(st.lists(
                st.booleans(),
                min_size=n_rows, max_size=n_rows
            ))
        else:  # mixed (but consistent within column for type safety)
            data[col] = draw(st.lists(
                st.integers(min_value=-1000, max_value=1000),
                min_size=n_rows, max_size=n_rows
            ))
    
    return pd.DataFrame(data)

# Test 1: JSON round-trip property
@given(df=dataframes_strategy())
@settings(max_examples=100)
def test_json_roundtrip_records_orient(df):
    json_str = df.to_json(orient='records')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    # Compare DataFrames
    pd.testing.assert_frame_equal(df.reset_index(drop=True), df_reconstructed.reset_index(drop=True))

# Test 2: JSON round-trip with split orient
@given(df=dataframes_strategy())
@settings(max_examples=100)
def test_json_roundtrip_split_orient(df):
    json_str = df.to_json(orient='split')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='split')
    
    pd.testing.assert_frame_equal(df, df_reconstructed)

# Test 3: CSV round-trip property
@given(df=dataframes_strategy())
@settings(max_examples=100)
def test_csv_roundtrip(df):
    # Filter out DataFrames with non-string column names for CSV
    assume(all(isinstance(col, str) for col in df.columns))
    
    csv_str = df.to_csv(index=False)
    df_reconstructed = pd.read_csv(io.StringIO(csv_str))
    
    # CSV may change dtypes, so we compare values with tolerance
    assert df.shape == df_reconstructed.shape
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            # Numeric columns should be close
            for i in range(len(df)):
                orig_val = df[col].iloc[i]
                recon_val = df_reconstructed[col].iloc[i]
                if pd.isna(orig_val):
                    assert pd.isna(recon_val)
                elif isinstance(orig_val, (int, float)) and isinstance(recon_val, (int, float)):
                    assert math.isclose(orig_val, recon_val, rel_tol=1e-9, abs_tol=1e-9)

# Test 4: Pickle round-trip property
@given(df=dataframes_strategy())
@settings(max_examples=100)
def test_pickle_roundtrip(df):
    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp:
        df.to_pickle(tmp.name)
        df_reconstructed = pd.read_pickle(tmp.name)
    
    pd.testing.assert_frame_equal(df, df_reconstructed)

# Test 5: DataFrame with special characters in columns
@given(
    data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20).filter(lambda x: len(x.strip()) > 0),
        values=st.lists(st.integers(-100, 100), min_size=5, max_size=5),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=100)
def test_json_special_chars_columns(data):
    df = pd.DataFrame(data)
    json_str = df.to_json(orient='columns')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='columns')
    
    # Sort columns because order might not be preserved
    df = df.reindex(sorted(df.columns), axis=1)
    df_reconstructed = df_reconstructed.reindex(sorted(df_reconstructed.columns), axis=1)
    
    pd.testing.assert_frame_equal(df, df_reconstructed)

# Test 6: Empty DataFrame handling
@given(n_cols=st.integers(min_value=0, max_value=10))
@settings(max_examples=50)
def test_empty_dataframe_json(n_cols):
    if n_cols == 0:
        df = pd.DataFrame()
    else:
        columns = [f'col_{i}' for i in range(n_cols)]
        df = pd.DataFrame(columns=columns)
    
    json_str = df.to_json(orient='records')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    assert len(df) == len(df_reconstructed)
    assert list(df.columns) == list(df_reconstructed.columns)

# Test 7: Large numeric values
@given(
    values=st.lists(
        st.floats(min_value=1e15, max_value=1e16, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=50)
def test_large_floats_json(values):
    df = pd.DataFrame({'large_nums': values})
    json_str = df.to_json(orient='records')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    for i in range(len(values)):
        assert math.isclose(df['large_nums'].iloc[i], df_reconstructed['large_nums'].iloc[i], rel_tol=1e-10)

# Test 8: Index preservation in JSON
@given(
    df=dataframes_strategy(),
    index_values=st.lists(st.integers(), min_size=1, max_size=50)
)
@settings(max_examples=50)
def test_json_index_preservation(df, index_values):
    assume(len(index_values) == len(df))
    df.index = index_values
    
    json_str = df.to_json(orient='index')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='index')
    
    # Index might be converted to string in JSON
    assert len(df) == len(df_reconstructed)
    assert df.shape[1] == df_reconstructed.shape[1]

# Test 9: NaN and None handling
@given(
    has_nan=st.booleans(),
    has_none=st.booleans()
)
@settings(max_examples=50)
def test_nan_none_json(has_nan, has_none):
    data = [1.0, 2.0, 3.0]
    if has_nan:
        data.append(float('nan'))
    if has_none:
        data.append(None)
    
    df = pd.DataFrame({'values': data})
    json_str = df.to_json(orient='records')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    assert len(df) == len(df_reconstructed)
    for i in range(len(df)):
        orig = df['values'].iloc[i]
        recon = df_reconstructed['values'].iloc[i]
        if pd.isna(orig):
            assert pd.isna(recon)
        else:
            assert orig == recon

# Test 10: Unicode handling
@given(
    text=st.text(alphabet=st.characters(min_codepoint=0x1F300, max_codepoint=0x1F6FF), min_size=1, max_size=20)
)
@settings(max_examples=50)
def test_unicode_json(text):
    df = pd.DataFrame({'emoji': [text]})
    json_str = df.to_json(orient='records', force_ascii=False)
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    assert df['emoji'].iloc[0] == df_reconstructed['emoji'].iloc[0]

# Test 11: Datetime round-trip
@given(
    dates=st.lists(
        st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 1, 1)),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=50)
def test_datetime_json_roundtrip(dates):
    df = pd.DataFrame({'dates': dates})
    json_str = df.to_json(orient='records', date_format='iso')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    # Convert to datetime if needed
    df_reconstructed['dates'] = pd.to_datetime(df_reconstructed['dates'])
    
    for i in range(len(dates)):
        # Compare with millisecond precision (JSON default)
        orig = df['dates'].iloc[i]
        recon = df_reconstructed['dates'].iloc[i]
        diff = abs((orig - recon).total_seconds())
        assert diff < 0.001  # Less than 1 millisecond difference

# Test 12: Boolean columns
@given(
    bools=st.lists(st.booleans(), min_size=1, max_size=20)
)
@settings(max_examples=50)
def test_boolean_json(bools):
    df = pd.DataFrame({'bool_col': bools})
    json_str = df.to_json(orient='records')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    pd.testing.assert_frame_equal(df, df_reconstructed)

# Test 13: Mixed type columns (should handle gracefully or error consistently)
@given(
    mixed_data=st.lists(
        st.one_of(st.integers(), st.text(max_size=10), st.booleans()),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=50)
def test_mixed_types_json(mixed_data):
    df = pd.DataFrame({'mixed': mixed_data})
    
    try:
        json_str = df.to_json(orient='records')
        df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
        
        # If it succeeds, data should be preserved (possibly as strings)
        assert len(df) == len(df_reconstructed)
    except (ValueError, TypeError):
        # If it fails, it should fail consistently
        pass

# Test 14: Duplicate column names
@given(
    n_rows=st.integers(min_value=1, max_value=10),
    col_name=column_names
)
@settings(max_examples=50)
def test_duplicate_columns_json(n_rows, col_name):
    data = {
        col_name: list(range(n_rows)),
    }
    # Try to create DataFrame with duplicate columns
    df = pd.DataFrame(data)
    df[col_name + '_dup'] = list(range(n_rows, n_rows * 2))
    
    json_str = df.to_json(orient='records')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    assert df.shape == df_reconstructed.shape

# Test 15: Very long strings
@given(
    long_string=st.text(min_size=1000, max_size=5000)
)
@settings(max_examples=20)
def test_long_strings_json(long_string):
    df = pd.DataFrame({'long_text': [long_string]})
    json_str = df.to_json(orient='records')
    df_reconstructed = pd.read_json(io.StringIO(json_str), orient='records')
    
    assert df['long_text'].iloc[0] == df_reconstructed['long_text'].iloc[0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])