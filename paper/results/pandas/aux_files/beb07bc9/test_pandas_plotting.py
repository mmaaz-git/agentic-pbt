import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, settings, assume
import pytest
from pandas.plotting import (
    bootstrap_plot, lag_plot, autocorrelation_plot,
    andrews_curves, parallel_coordinates, radviz,
    scatter_matrix
)


# Property 1: bootstrap_plot's size parameter must be <= series length
@given(
    series_length=st.integers(min_value=1, max_value=100),
    size=st.integers(min_value=1, max_value=200),
    samples=st.integers(min_value=1, max_value=50)
)
def test_bootstrap_plot_size_constraint(series_length, size, samples):
    """Bootstrap plot's size parameter should be validated against series length."""
    series = pd.Series(np.random.randn(series_length))
    
    if size > series_length:
        # This should raise an error
        with pytest.raises((ValueError, AssertionError, IndexError)):
            fig = bootstrap_plot(series, size=size, samples=samples)
    else:
        # This should work
        fig = bootstrap_plot(series, size=size, samples=samples)
        assert fig is not None


# Property 2: Functions requiring class_column should validate it exists
@given(
    df_rows=st.integers(min_value=1, max_value=50),
    df_cols=st.integers(min_value=2, max_value=10),
    class_column=st.text(min_size=1, max_size=20, alphabet=st.characters(categories=['L', 'N']))
)
def test_classification_plots_class_column_validation(df_rows, df_cols, class_column):
    """Classification visualization functions should validate class_column exists."""
    
    # Create a DataFrame without the class_column
    columns = [f'col_{i}' for i in range(df_cols)]
    df = pd.DataFrame(np.random.randn(df_rows, df_cols), columns=columns)
    
    # These should fail when class_column doesn't exist
    for plot_func in [andrews_curves, parallel_coordinates, radviz]:
        if class_column not in df.columns:
            with pytest.raises((KeyError, ValueError)):
                plot_func(df, class_column)


# Property 3: lag_plot with negative lag should either work or raise clear error
@given(
    series_length=st.integers(min_value=2, max_value=100),
    lag=st.integers(min_value=-100, max_value=100)
)
def test_lag_plot_negative_lag(series_length, lag):
    """lag_plot should handle negative lag values properly."""
    series = pd.Series(np.random.randn(series_length))
    
    # Test if negative lag is handled
    if lag < 0 or lag >= series_length:
        # Should either work or raise a clear error
        try:
            ax = lag_plot(series, lag=lag)
            # If it works, check that it returns an axes
            assert ax is not None
        except (ValueError, IndexError, TypeError) as e:
            # Error is acceptable for invalid lag
            pass
    else:
        ax = lag_plot(series, lag=lag)
        assert ax is not None


# Property 4: scatter_matrix diagonal parameter validation
@given(
    df_rows=st.integers(min_value=2, max_value=50),
    df_cols=st.integers(min_value=2, max_value=5),
    diagonal=st.sampled_from(['hist', 'kde', None, 'invalid'])
)
def test_scatter_matrix_diagonal_validation(df_rows, df_cols, diagonal):
    """scatter_matrix should validate the diagonal parameter."""
    df = pd.DataFrame(np.random.randn(df_rows, df_cols))
    
    if diagonal in ['hist', 'kde', None]:
        # These should work
        axes = scatter_matrix(df, diagonal=diagonal)
        assert axes is not None
    elif diagonal == 'invalid':
        # This should raise an error
        with pytest.raises((ValueError, KeyError, TypeError)):
            scatter_matrix(df, diagonal=diagonal)


# Property 5: Empty DataFrame handling
@given(
    plot_type=st.sampled_from(['andrews', 'parallel', 'radviz'])
)
def test_empty_dataframe_handling(plot_type):
    """Plotting functions should handle empty DataFrames gracefully."""
    empty_df = pd.DataFrame()
    
    plot_funcs = {
        'andrews': andrews_curves,
        'parallel': parallel_coordinates,
        'radviz': radviz
    }
    
    func = plot_funcs[plot_type]
    
    # Should raise an error for empty DataFrame
    with pytest.raises((KeyError, ValueError, IndexError)):
        func(empty_df, 'class')


# Property 6: autocorrelation_plot with series of length 1
@given(value=st.floats(allow_nan=False, allow_infinity=False))
def test_autocorrelation_plot_single_value(value):
    """autocorrelation_plot should handle single-value series properly."""
    series = pd.Series([value])
    
    # Should either work or raise a clear error
    try:
        ax = autocorrelation_plot(series)
        assert ax is not None
    except (ValueError, IndexError, ZeroDivisionError) as e:
        # Error is acceptable for single value
        pass


# Property 7: Samples parameter in andrews_curves should be positive
@given(
    samples=st.integers(min_value=-100, max_value=100)
)
def test_andrews_curves_samples_validation(samples):
    """andrews_curves should validate that samples is positive."""
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6],
        'class': ['a', 'b', 'c']
    })
    
    if samples <= 0:
        with pytest.raises((ValueError, TypeError)):
            andrews_curves(df, 'class', samples=samples)
    else:
        ax = andrews_curves(df, 'class', samples=samples)
        assert ax is not None


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])