"""Property-based tests for scipy.constants using Hypothesis"""

import math
import numpy as np
from hypothesis import given, assume, strategies as st, settings
import scipy.constants as sc
import pytest


# Strategy for reasonable temperature values
reasonable_temps = st.floats(min_value=-273.0, max_value=1e6, allow_nan=False, allow_infinity=False)

# Strategy for positive wavelengths/frequencies
positive_floats = st.floats(min_value=1e-20, max_value=1e20, allow_nan=False, allow_infinity=False)

# Strategy for temperature scale names
temp_scales = st.sampled_from(['Celsius', 'celsius', 'C', 'c', 
                                'Kelvin', 'kelvin', 'K', 'k',
                                'Fahrenheit', 'fahrenheit', 'F', 'f',
                                'Rankine', 'rankine', 'R', 'r'])


@given(val=reasonable_temps, scale1=temp_scales, scale2=temp_scales)
@settings(max_examples=1000)
def test_temperature_conversion_round_trip(val, scale1, scale2):
    """
    Test that converting temperature from scale1 to scale2 and back gives the original value.
    
    This is a fundamental round-trip property: f^-1(f(x)) = x
    """
    # Skip if temperature is invalid for the scale
    if scale1.lower() in ['kelvin', 'k'] and val < 0:
        assume(False)
    if scale1.lower() in ['rankine', 'r'] and val < 0:
        assume(False)
    
    # Convert from scale1 to scale2
    intermediate = sc.convert_temperature(val, scale1, scale2)
    
    # Convert back from scale2 to scale1
    result = sc.convert_temperature(intermediate, scale2, scale1)
    
    # Check the round-trip property
    assert math.isclose(result, val, rel_tol=1e-10, abs_tol=1e-10), \
        f"Round-trip failed: {val} -> {intermediate} -> {result} for {scale1} -> {scale2} -> {scale1}"


@given(wavelength=positive_floats)
@settings(max_examples=1000)
def test_lambda2nu_nu2lambda_round_trip(wavelength):
    """
    Test that converting wavelength to frequency and back gives the original value.
    
    This tests the round-trip property: nu2lambda(lambda2nu(λ)) = λ
    """
    frequency = sc.lambda2nu(wavelength)
    result = sc.nu2lambda(frequency)
    
    # Use relative tolerance due to floating point arithmetic
    assert math.isclose(result, wavelength, rel_tol=1e-14), \
        f"Round-trip failed: {wavelength} -> {frequency} -> {result}"


@given(frequency=positive_floats)
@settings(max_examples=1000)
def test_nu2lambda_lambda2nu_round_trip(frequency):
    """
    Test that converting frequency to wavelength and back gives the original value.
    
    This tests the round-trip property: lambda2nu(nu2lambda(ν)) = ν
    """
    wavelength = sc.nu2lambda(frequency)
    result = sc.lambda2nu(wavelength)
    
    # Use relative tolerance due to floating point arithmetic
    assert math.isclose(result, frequency, rel_tol=1e-14), \
        f"Round-trip failed: {frequency} -> {wavelength} -> {result}"


@given(wavelength=positive_floats)
@settings(max_examples=500)
def test_lambda_nu_product_equals_c(wavelength):
    """
    Test that λ * ν = c (speed of light)
    
    This is the fundamental relationship between wavelength and frequency.
    """
    frequency = sc.lambda2nu(wavelength)
    product = wavelength * frequency
    
    # The product should equal the speed of light
    assert math.isclose(product, sc.c, rel_tol=1e-14), \
        f"λ * ν != c: {wavelength} * {frequency} = {product}, expected {sc.c}"


# Test consistency of physical constants dictionary
def test_physical_constants_consistency():
    """
    Test that value(), unit(), and precision() functions are consistent with physical_constants.
    """
    # Get a sample of keys from physical_constants
    sample_keys = list(sc.physical_constants.keys())[:20]
    
    for key in sample_keys:
        # Get values from the dictionary directly
        dict_value, dict_unit, dict_uncertainty = sc.physical_constants[key]
        
        # Get values from the functions
        func_value = sc.value(key)
        func_unit = sc.unit(key)
        func_precision = sc.precision(key)
        
        # Check consistency
        assert func_value == dict_value, f"Value mismatch for {key}"
        assert func_unit == dict_unit, f"Unit mismatch for {key}"
        
        # Precision is calculated as uncertainty/value
        if dict_value != 0:
            expected_precision = dict_uncertainty / dict_value
            assert math.isclose(func_precision, expected_precision, rel_tol=1e-10), \
                f"Precision mismatch for {key}: {func_precision} != {expected_precision}"


@given(st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
def test_find_function_substring_property(substring):
    """
    Test that find() returns only keys containing the substring.
    """
    results = sc.find(substring)
    
    if results is not None:  # find() returns None if disp=True
        for key in results:
            assert substring.lower() in key.lower(), \
                f"Key '{key}' returned by find('{substring}') but doesn't contain substring"


# Test temperature conversion edge cases
@given(val=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_kelvin_to_kelvin_identity(val):
    """
    Test that converting from Kelvin to Kelvin returns the same value.
    
    This is the identity property: f(x) = x when converting to the same scale.
    """
    assume(val >= 0)  # Kelvin can't be negative
    
    result = sc.convert_temperature(val, 'Kelvin', 'Kelvin')
    assert result == val, f"Kelvin to Kelvin conversion changed value: {val} -> {result}"


@given(val=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_celsius_to_celsius_identity(val):
    """
    Test that converting from Celsius to Celsius returns the same value.
    """
    result = sc.convert_temperature(val, 'Celsius', 'Celsius')
    assert result == val, f"Celsius to Celsius conversion changed value: {val} -> {result}"


# Test arrays
@given(wavelengths=st.lists(positive_floats, min_size=1, max_size=10))
def test_lambda2nu_with_arrays(wavelengths):
    """
    Test that lambda2nu works correctly with arrays.
    """
    arr = np.array(wavelengths)
    frequencies = sc.lambda2nu(arr)
    
    # Check each element
    for i, wavelength in enumerate(wavelengths):
        expected = sc.c / wavelength
        assert math.isclose(frequencies[i], expected, rel_tol=1e-14), \
            f"Array element {i} incorrect: {frequencies[i]} != {expected}"


@given(temps=st.lists(reasonable_temps, min_size=1, max_size=10), 
       scale1=temp_scales, scale2=temp_scales)
def test_temperature_conversion_with_arrays(temps, scale1, scale2):
    """
    Test that temperature conversion works correctly with arrays.
    """
    # Filter out invalid temperatures for the scale
    if scale1.lower() in ['kelvin', 'k', 'rankine', 'r']:
        temps = [t for t in temps if t >= 0]
        if not temps:
            assume(False)
    
    arr = np.array(temps)
    result = sc.convert_temperature(arr, scale1, scale2)
    
    # Check each element
    for i, temp in enumerate(temps):
        expected = sc.convert_temperature(temp, scale1, scale2)
        assert math.isclose(result[i], expected, rel_tol=1e-10, abs_tol=1e-10), \
            f"Array element {i} incorrect: {result[i]} != {expected}"


# Test specific temperature conversion formulas
def test_celsius_kelvin_conversion_formula():
    """
    Test the documented formula: K = C + 273.15
    """
    test_values = [-273.15, -100, 0, 25, 100, 1000]
    
    for celsius in test_values:
        kelvin = sc.convert_temperature(celsius, 'Celsius', 'Kelvin')
        expected = celsius + sc.zero_Celsius
        assert math.isclose(kelvin, expected, rel_tol=1e-14), \
            f"C to K formula incorrect: {celsius}°C -> {kelvin}K, expected {expected}K"


def test_fahrenheit_celsius_conversion_formula():
    """
    Test the documented formula: C = (F - 32) * 5/9
    """
    test_values = [-40, 0, 32, 100, 212]
    
    for fahrenheit in test_values:
        celsius = sc.convert_temperature(fahrenheit, 'Fahrenheit', 'Celsius')
        expected = (fahrenheit - 32) * 5 / 9
        assert math.isclose(celsius, expected, rel_tol=1e-14), \
            f"F to C formula incorrect: {fahrenheit}°F -> {celsius}°C, expected {expected}°C"