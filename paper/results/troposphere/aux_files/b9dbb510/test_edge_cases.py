"""Edge case tests for troposphere.evidently to find potential bugs"""

from hypothesis import given, strategies as st, settings, assume
import troposphere.evidently as evidently
import pytest
import sys


class TestValidatorEdgeCases:
    """Test edge cases in validator functions"""
    
    @given(st.one_of(
        st.just(float('inf')),
        st.just(float('-inf')),
        st.just(float('nan')),
        st.text(alphabet='🦄💀😈', min_size=1),  # Unicode edge cases
        st.just(''),
        st.just(' '),
        st.just('\n'),
        st.just('\t'),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    ))
    def test_boolean_unusual_inputs(self, value):
        """Test boolean with edge case inputs"""
        try:
            result = evidently.boolean(value)
            # If successful, must be a bool
            assert isinstance(result, bool)
            # Should only succeed for known valid values
            assert value in [True, False, 1, 0, "1", "0", "true", "false", "True", "False"]
        except ValueError:
            # Expected for invalid inputs
            pass
    
    @given(st.one_of(
        st.just(sys.maxsize),
        st.just(-sys.maxsize),
        st.just(2**100),  # Very large number
        st.just(10**308),  # Near float max
        st.just('inf'),
        st.just('-inf'),
        st.just('nan'),
        st.just('NaN'),
        st.just('Infinity'),
        st.just('-Infinity')
    ))
    def test_double_extreme_values(self, value):
        """Test double with extreme numeric values"""
        try:
            result = evidently.double(value)
            # Should return the same value
            assert result == value
            # Verify it can actually be converted to float
            float_val = float(result)
        except (ValueError, OverflowError):
            # Some values might not be valid
            pass
    
    @settings(max_examples=500)
    @given(st.one_of(
        st.floats(min_value=2**53, max_value=2**60),  # Beyond exact int representation
        st.just(9007199254740993.0),  # Just beyond 2^53 + 1
        st.decimals(min_value=0, max_value=1e20).map(str),
        st.text(alphabet='0123456789.eE+-', min_size=1, max_size=50)
    ))
    def test_integer_float_precision_loss(self, value):
        """Test integer with values that might lose precision"""
        try:
            result = evidently.integer(value)
            # Must be returnable
            assert result == value
        except (ValueError, TypeError, OverflowError):
            # Expected for non-integer convertible
            pass


class TestAWSObjectEdgeCases:
    """Test edge cases in AWS object classes"""
    
    @given(
        st.text(alphabet='🦄💀😈\n\t\r', min_size=0, max_size=100),
        st.one_of(
            st.just(None),
            st.just(True), 
            st.just(False),
            st.just('true'),
            st.just('false'),
            st.just('True'),
            st.just('False'),
            st.just(1),
            st.just(0),
            st.just('1'),
            st.just('0'),
            st.just('yes'),
            st.just('no')
        )
    )
    def test_variation_with_unicode_and_bool_strings(self, name, bool_val):
        """Test VariationObject with unicode names and various boolean representations"""
        if not name.strip():
            # Empty names might fail validation
            return
            
        try:
            var = evidently.VariationObject(
                VariationName=name,
                BooleanValue=bool_val
            )
            result = var.to_dict()
            assert result['VariationName'] == name
            
            # Check if BooleanValue was properly converted
            if 'BooleanValue' in result:
                assert isinstance(result['BooleanValue'], bool)
        except (ValueError, TypeError):
            # Some values might not be valid booleans
            pass
    
    @given(st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(st.none(), st.text(), st.integers(), st.floats(), st.booleans()),
        min_size=0,
        max_size=10
    ))
    def test_arbitrary_kwargs_to_classes(self, kwargs):
        """Test what happens with arbitrary keyword arguments"""
        try:
            # Try to create objects with random kwargs
            var = evidently.VariationObject(**kwargs)
            # If successful, check to_dict
            result = var.to_dict()
            # Required field must be present
            if 'VariationName' in result:
                assert result['VariationName'] is not None
        except (TypeError, ValueError):
            # Expected for invalid arguments
            pass
    
    @settings(max_examples=200)
    @given(
        name=st.text(min_size=1, max_size=100),
        value_combo=st.lists(
            st.tuples(
                st.sampled_from(['BooleanValue', 'DoubleValue', 'LongValue', 'StringValue']),
                st.one_of(st.booleans(), st.floats(), st.integers(), st.text())
            ),
            min_size=2,
            max_size=4
        )
    )
    def test_multiple_value_types_simultaneously(self, name, value_combo):
        """Test VariationObject with multiple value types set simultaneously"""
        kwargs = {'VariationName': name}
        for field, value in value_combo:
            kwargs[field] = value
        
        try:
            var = evidently.VariationObject(**kwargs)
            result = var.to_dict()
            
            # All provided fields should be in result
            assert 'VariationName' in result
            
            # Check which fields made it through
            for field, value in value_combo:
                if field in result:
                    # The value should match or be validated
                    if field == 'BooleanValue':
                        assert isinstance(result[field], bool)
                    elif field in ['DoubleValue', 'LongValue']:
                        # Should be numeric
                        assert isinstance(result[field], (int, float))
                    elif field == 'StringValue':
                        assert isinstance(result[field], str)
        except (ValueError, TypeError):
            # Some combinations might not be valid
            pass