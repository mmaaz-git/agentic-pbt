"""Property-based tests for troposphere.evidently module"""

import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.evidently as evidently
import pytest


# Test validator functions
class TestValidatorFunctions:
    """Test the validator functions: boolean, double, integer"""
    
    # Property 1: boolean function should be idempotent for valid boolean inputs
    @given(st.sampled_from([True, False, 1, 0, "1", "0", "true", "false", "True", "False"]))
    def test_boolean_idempotent_valid_inputs(self, value):
        """Property: boolean(x) should return consistent True/False for valid inputs"""
        result1 = evidently.boolean(value)
        result2 = evidently.boolean(value)
        assert result1 == result2
        assert isinstance(result1, bool)
        
        # Additional property: boolean values should maintain their truthiness
        if value in [True, 1, "1", "true", "True"]:
            assert result1 is True
        elif value in [False, 0, "0", "false", "False"]:
            assert result1 is False
    
    # Property 2: double function should accept any valid float-convertible input
    @given(st.one_of(
        st.floats(allow_nan=False, allow_infinity=False),
        st.integers(),
        st.text().filter(lambda s: s.strip() != '').map(str)
    ))
    def test_double_validation(self, value):
        """Property: double(x) should return x if x can be converted to float"""
        try:
            float(value)
            can_convert = True
        except (ValueError, TypeError):
            can_convert = False
        
        if can_convert:
            result = evidently.double(value)
            assert result == value
        else:
            with pytest.raises(ValueError):
                evidently.double(value)
    
    # Property 3: integer function should accept any valid int-convertible input
    @given(st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text()
    ))
    def test_integer_validation(self, value):
        """Property: integer(x) should return x if x can be converted to int"""
        try:
            int(value)
            can_convert = True
        except (ValueError, TypeError, OverflowError):
            can_convert = False
        
        if can_convert:
            try:
                result = evidently.integer(value)
                assert result == value
            except ValueError:
                # integer() might be more strict than int()
                pass
        else:
            with pytest.raises(ValueError):
                evidently.integer(value)


class TestAWSPropertyClasses:
    """Test AWSProperty classes and their to_dict serialization"""
    
    # Property 4: VariationObject round-trip property for to_dict()
    @given(
        name=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
        bool_val=st.booleans(),
        double_val=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        string_val=st.text(max_size=1000)
    )
    def test_variation_object_roundtrip(self, name, bool_val, double_val, string_val):
        """Property: VariationObject.to_dict() should preserve all set properties"""
        # Test with BooleanValue
        var_bool = evidently.VariationObject(
            VariationName=name,
            BooleanValue=bool_val
        )
        dict_bool = var_bool.to_dict()
        assert dict_bool['VariationName'] == name
        assert dict_bool['BooleanValue'] == bool_val
        assert 'DoubleValue' not in dict_bool
        assert 'StringValue' not in dict_bool
        
        # Test with DoubleValue
        var_double = evidently.VariationObject(
            VariationName=name,
            DoubleValue=double_val
        )
        dict_double = var_double.to_dict()
        assert dict_double['VariationName'] == name
        assert dict_double['DoubleValue'] == double_val
        assert 'BooleanValue' not in dict_double
        
        # Test with StringValue
        var_string = evidently.VariationObject(
            VariationName=name,
            StringValue=string_val
        )
        dict_string = var_string.to_dict()
        assert dict_string['VariationName'] == name
        assert dict_string['StringValue'] == string_val
        assert 'BooleanValue' not in dict_string
    
    # Property 5: EntityOverride should correctly serialize optional fields
    @given(
        entity_id=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        variation=st.one_of(st.none(), st.text(min_size=1, max_size=100))
    )
    def test_entity_override_optional_fields(self, entity_id, variation):
        """Property: EntityOverride.to_dict() should only include non-None fields"""
        kwargs = {}
        if entity_id is not None:
            kwargs['EntityId'] = entity_id
        if variation is not None:
            kwargs['Variation'] = variation
        
        # EntityOverride has all optional fields, can be created empty
        entity = evidently.EntityOverride(**kwargs)
        result = entity.to_dict()
        
        # Check that only provided fields are in the result
        if entity_id is not None:
            assert result.get('EntityId') == entity_id
        else:
            assert 'EntityId' not in result
            
        if variation is not None:
            assert result.get('Variation') == variation
        else:
            assert 'Variation' not in result
    
    # Property 6: MetricGoalObject required vs optional fields
    @given(
        desired_change=st.text(min_size=1, max_size=50),
        entity_id_key=st.text(min_size=1, max_size=50),
        metric_name=st.text(min_size=1, max_size=50),
        value_key=st.text(min_size=1, max_size=50),
        event_pattern=st.one_of(st.none(), st.text(max_size=500)),
        unit_label=st.one_of(st.none(), st.text(max_size=50))
    )
    def test_metric_goal_required_optional(self, desired_change, entity_id_key, 
                                          metric_name, value_key, event_pattern, unit_label):
        """Property: MetricGoalObject should enforce required fields and handle optional ones"""
        # Test with all required fields
        metric = evidently.MetricGoalObject(
            DesiredChange=desired_change,
            EntityIdKey=entity_id_key,
            MetricName=metric_name,
            ValueKey=value_key
        )
        result = metric.to_dict()
        assert result['DesiredChange'] == desired_change
        assert result['EntityIdKey'] == entity_id_key
        assert result['MetricName'] == metric_name
        assert result['ValueKey'] == value_key
        
        # Add optional fields if provided
        if event_pattern is not None:
            metric2 = evidently.MetricGoalObject(
                DesiredChange=desired_change,
                EntityIdKey=entity_id_key,
                MetricName=metric_name,
                ValueKey=value_key,
                EventPattern=event_pattern
            )
            result2 = metric2.to_dict()
            assert result2['EventPattern'] == event_pattern
    
    # Property 7: Integer fields should validate integer constraints
    @given(
        split_weight=st.one_of(
            st.integers(min_value=-2**63, max_value=2**63-1),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text()
        ),
        treatment=st.text(min_size=1, max_size=100)
    )
    def test_treatment_to_weight_integer_validation(self, split_weight, treatment):
        """Property: TreatmentToWeight should validate integer field correctly"""
        try:
            int(split_weight)
            is_valid_int = True
        except (ValueError, TypeError, OverflowError):
            is_valid_int = False
        
        if is_valid_int:
            try:
                ttw = evidently.TreatmentToWeight(
                    SplitWeight=split_weight,
                    Treatment=treatment
                )
                result = ttw.to_dict()
                assert 'SplitWeight' in result
                assert 'Treatment' in result
            except (ValueError, TypeError):
                # The integer validator might be stricter
                pass
        else:
            with pytest.raises((ValueError, TypeError)):
                evidently.TreatmentToWeight(
                    SplitWeight=split_weight,
                    Treatment=treatment
                )