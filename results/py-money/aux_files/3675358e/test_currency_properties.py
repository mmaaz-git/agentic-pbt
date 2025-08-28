from hypothesis import given, strategies as st, assume
from money.currency import Currency, CurrencyHelper
from collections import Counter
import math


@given(st.sampled_from(Currency))
def test_currency_has_complete_data(currency):
    """Every Currency enum value should have complete data in _CURRENCY_DATA"""
    assert currency in CurrencyHelper._CURRENCY_DATA
    
    data = CurrencyHelper._CURRENCY_DATA[currency]
    assert 'display_name' in data
    assert 'numeric_code' in data
    assert 'default_fraction_digits' in data
    assert 'sub_unit' in data
    
    assert isinstance(data['display_name'], str)
    assert isinstance(data['numeric_code'], int)
    assert isinstance(data['default_fraction_digits'], int)
    assert isinstance(data['sub_unit'], int)


@given(st.sampled_from(Currency))
def test_valid_data_ranges(currency):
    """Currency data should be within reasonable bounds"""
    data = CurrencyHelper._CURRENCY_DATA[currency]
    
    # Numeric codes should be 3-digit numbers (or close to it)
    assert 0 < data['numeric_code'] < 1000
    
    # Decimal precision should be between 0 and 4 (most currencies use 0-3)
    assert 0 <= data['default_fraction_digits'] <= 4
    
    # Sub unit should be positive
    assert data['sub_unit'] > 0
    
    # Sub unit should be reasonable (1, 5, 10, 100, 1000 are common)
    assert data['sub_unit'] in [1, 5, 10, 100, 1000]


@given(st.sampled_from(Currency))
def test_decimal_precision_sub_unit_consistency(currency):
    """Decimal precision and sub_unit should be consistent"""
    data = CurrencyHelper._CURRENCY_DATA[currency]
    decimal_precision = data['default_fraction_digits']
    sub_unit = data['sub_unit']
    
    # For most currencies, sub_unit should be 10^decimal_precision
    # But there are exceptions like MGA (5 sub_units) and MRO (5 sub_units)
    if sub_unit not in [1, 5]:
        # For standard currencies, sub_unit should match 10^decimal_precision
        expected_sub_unit = 10 ** decimal_precision
        assert sub_unit == expected_sub_unit, f"Currency {currency.name}: sub_unit={sub_unit}, expected={expected_sub_unit} for decimal_precision={decimal_precision}"


def test_numeric_code_uniqueness():
    """Numeric codes should be mostly unique (with known exceptions)"""
    all_codes = []
    for currency in Currency:
        data = CurrencyHelper._CURRENCY_DATA[currency]
        all_codes.append((currency.name, data['numeric_code']))
    
    # Count occurrences
    code_counts = Counter(code for _, code in all_codes)
    
    # Find duplicates
    duplicates = {code: count for code, count in code_counts.items() if count > 1}
    
    # Known duplicates: XBD and XFU both have 958
    # Let's check if there are unexpected duplicates
    for code, count in duplicates.items():
        currencies_with_code = [name for name, c in all_codes if c == code]
        # Allow the known duplicate
        if code == 958:
            assert set(currencies_with_code) == {'XBD', 'XFU'}
        else:
            # No other duplicates should exist
            assert count == 1, f"Unexpected duplicate numeric code {code} for currencies: {currencies_with_code}"


@given(st.sampled_from(Currency))
def test_helper_methods_consistency(currency):
    """CurrencyHelper methods should return data consistent with _CURRENCY_DATA"""
    decimal_precision = CurrencyHelper.decimal_precision_for_currency(currency)
    sub_unit = CurrencyHelper.sub_unit_for_currency(currency)
    
    assert decimal_precision == CurrencyHelper._CURRENCY_DATA[currency]['default_fraction_digits']
    assert sub_unit == CurrencyHelper._CURRENCY_DATA[currency]['sub_unit']


@given(st.sampled_from(Currency))
def test_currency_enum_value_matches_name(currency):
    """Currency enum values should match their names"""
    assert currency.value == currency.name