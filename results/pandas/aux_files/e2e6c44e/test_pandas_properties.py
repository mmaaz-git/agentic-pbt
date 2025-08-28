import math
import numpy as np
import pandas as pd
from hypothesis import given, strategies as st, assume, settings
import pytest


@given(st.lists(st.one_of(
    st.integers(min_value=-1000000, max_value=1000000),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.text(min_size=0, max_size=100),
)))
def test_unique_length_invariant(values):
    """Test that unique values never exceed original length"""
    if not values:
        return
    
    result = pd.unique(values)
    assert len(result) <= len(values)


@given(st.lists(st.one_of(
    st.integers(min_value=-1000000, max_value=1000000),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.text(min_size=0, max_size=100),
)))
def test_unique_preserves_values(values):
    """Test that all unique values come from original"""
    if not values:
        return
    
    result = pd.unique(values)
    original_set = set(values) if all(isinstance(v, (int, float, str)) for v in values) else values
    
    for val in result:
        if pd.notna(val):
            assert val in values or (isinstance(val, float) and math.isnan(val))


@given(st.lists(st.one_of(
    st.integers(min_value=-1000000, max_value=1000000),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=1, max_size=20),
), min_size=1))
def test_factorize_roundtrip(values):
    """Test factorize can be reversed"""
    codes, uniques = pd.factorize(values)
    
    assert len(codes) == len(values)
    
    reconstructed = [uniques[code] if code >= 0 else np.nan for code in codes]
    
    for original, reconst in zip(values, reconstructed):
        if pd.isna(reconst):
            assert pd.isna(original) or original != original
        else:
            assert original == reconst or (isinstance(original, float) and isinstance(reconst, float) and math.isclose(original, reconst, rel_tol=1e-9))


@given(st.lists(st.one_of(
    st.integers(min_value=-100, max_value=100),
    st.text(min_size=1, max_size=10),
), min_size=1))
def test_value_counts_sum_invariant(values):
    """Test that value counts sum equals original length"""
    counts = pd.value_counts(values, dropna=False)
    assert counts.sum() == len(values)


@given(st.lists(st.one_of(
    st.integers(min_value=-100, max_value=100),
    st.text(min_size=1, max_size=10),
), min_size=1))
def test_value_counts_keys_are_unique(values):
    """Test that value_counts keys are unique values from input"""
    counts = pd.value_counts(values, dropna=False)
    unique_vals = pd.unique(values)
    
    for key in counts.index:
        assert key in values or pd.isna(key)


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000), min_size=2),
    st.integers(min_value=2, max_value=10)
)
def test_cut_qcut_preserve_length(values, bins):
    """Test that cut and qcut preserve input length"""
    assume(bins <= len(values))
    
    cut_result = pd.cut(values, bins=bins)
    assert len(cut_result) == len(values)
    
    qcut_result = pd.qcut(values, q=bins, duplicates='drop')
    assert len(qcut_result) == len(values)


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), min_size=3, max_size=100),
    st.integers(min_value=2, max_value=5)
)
def test_qcut_balanced_bins(values, q):
    """Test that qcut creates approximately balanced bins"""
    assume(len(set(values)) >= q)
    
    result = pd.qcut(values, q=q, duplicates='drop')
    counts = result.value_counts()
    
    if len(counts) > 1:
        min_count = counts.min()
        max_count = counts.max()
        assert max_count - min_count <= len(values) // 2


@given(st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=100))
def test_series_index_invariants(values):
    """Test Series index properties"""
    s = pd.Series(values)
    
    assert len(s) == len(values)
    assert len(s.index) == len(values)
    assert all(s.iloc[i] == values[i] for i in range(len(values)))


@given(
    st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=50),
    st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=50)
)
def test_concat_length_invariant(list1, list2):
    """Test that concat preserves total length"""
    s1 = pd.Series(list1)
    s2 = pd.Series(list2)
    
    result = pd.concat([s1, s2], ignore_index=True)
    assert len(result) == len(s1) + len(s2)


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6), min_size=1))
def test_series_arithmetic_identity(values):
    """Test arithmetic identities on Series"""
    s = pd.Series(values)
    
    result_add = s + 0
    assert all(math.isclose(a, b, rel_tol=1e-9) for a, b in zip(s, result_add))
    
    result_mul = s * 1
    assert all(math.isclose(a, b, rel_tol=1e-9) for a, b in zip(s, result_mul))
    
    result_sub = s - s
    assert all(math.isclose(val, 0, abs_tol=1e-9) for val in result_sub)


@given(st.lists(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=1, max_size=10)
), min_size=1))
def test_categorical_from_codes_roundtrip(values):
    """Test Categorical encoding round-trip"""
    cat = pd.Categorical(values)
    codes = cat.codes
    categories = cat.categories
    
    reconstructed = pd.Categorical.from_codes(codes, categories)
    
    assert len(cat) == len(reconstructed)
    for orig, recon in zip(cat, reconstructed):
        if pd.isna(orig):
            assert pd.isna(recon)
        else:
            assert orig == recon


@given(st.data())
def test_dataframe_transpose_involution(data):
    """Test that transpose is its own inverse"""
    nrows = data.draw(st.integers(min_value=1, max_value=20))
    ncols = data.draw(st.integers(min_value=1, max_value=20))
    
    values = [[data.draw(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100))
               for _ in range(ncols)] for _ in range(nrows)]
    
    df = pd.DataFrame(values)
    transposed_twice = df.T.T
    
    assert df.shape == transposed_twice.shape
    assert df.equals(transposed_twice)


@given(st.lists(st.dictionaries(
    st.text(min_size=1, max_size=5),
    st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text()),
    min_size=1,
    max_size=3
), min_size=1, max_size=10))
def test_json_normalize_basic(data):
    """Test json_normalize doesn't crash on valid input"""
    try:
        result = pd.json_normalize(data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(data)
    except Exception as e:
        if "Conflicting metadata" not in str(e):
            raise


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), min_size=2))
def test_series_rank_properties(values):
    """Test rank method properties"""
    s = pd.Series(values)
    ranks = s.rank()
    
    assert len(ranks) == len(s)
    assert ranks.min() >= 1.0
    assert ranks.max() <= len(s)


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1))
def test_series_idempotent_operations(values):
    """Test idempotent operations on Series"""
    s = pd.Series(values)
    
    abs_twice = s.abs().abs()
    abs_once = s.abs()
    assert abs_once.equals(abs_twice)
    
    clip_twice = s.clip(lower=0).clip(lower=0)
    clip_once = s.clip(lower=0)
    assert clip_once.equals(clip_twice)


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=0.1, max_value=1000), min_size=1))
def test_series_log_exp_roundtrip(values):
    """Test log-exp round trip"""
    s = pd.Series(values)
    
    result = np.exp(np.log(s))
    assert all(math.isclose(a, b, rel_tol=1e-9) for a, b in zip(s, result))


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1))
def test_series_shift_inverse(values):
    """Test shift operations are inverses"""
    s = pd.Series(values)
    
    shifted_right_left = s.shift(1).shift(-1)
    
    for i in range(1, len(s) - 1):
        assert s.iloc[i] == shifted_right_left.iloc[i]


@given(st.lists(st.one_of(
    st.integers(min_value=-100, max_value=100),
    st.floats(allow_nan=False, allow_infinity=False),
), min_size=1))
def test_series_fillna_completeness(values):
    """Test fillna removes all NaNs when using a value"""
    s = pd.Series(values)
    s.iloc[::2] = np.nan
    
    filled = s.fillna(0)
    assert not filled.isna().any()


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100), min_size=3))
def test_series_rolling_mean_bounds(values):
    """Test rolling mean stays within bounds"""
    s = pd.Series(values)
    window = min(3, len(values))
    
    rolling_mean = s.rolling(window=window, min_periods=1).mean()
    
    assert all(val >= s.min() - 1e-9 and val <= s.max() + 1e-9 
              for val in rolling_mean if pd.notna(val))