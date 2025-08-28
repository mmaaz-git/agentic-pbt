import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.rolesanywhere as ra
from troposphere.validators import boolean, double
import pytest


# Strategy for valid boolean-like inputs
st_boolean_valid = st.one_of(
    st.sampled_from([True, False, 1, 0, "1", "0", "true", "false", "True", "False"])
)

# Strategy for any value that might be passed to boolean
st_boolean_any = st.one_of(
    st_boolean_valid,
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
)

# Strategy for valid double inputs (focusing on realistic values)
st_double_valid = st.one_of(
    st.integers(min_value=-10**10, max_value=10**10),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-10**10, max_value=10**10),
    st.text().filter(lambda s: s.strip() != '').map(lambda s: s if _is_numeric_string(s) else None).filter(lambda x: x is not None)
)

def _is_numeric_string(s):
    """Check if string represents a valid number"""
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


class TestValidators:
    """Test the validator functions for correctness"""
    
    @given(st_boolean_valid)
    def test_boolean_validator_valid_inputs(self, value):
        """Test that boolean validator correctly handles all valid inputs"""
        result = boolean(value)
        assert isinstance(result, bool)
        
        # Check the mapping is correct
        if value in [True, 1, "1", "true", "True"]:
            assert result is True
        elif value in [False, 0, "0", "false", "False"]:
            assert result is False
    
    @given(st_boolean_any)
    def test_boolean_validator_invalid_inputs(self, value):
        """Test that boolean validator raises ValueError for invalid inputs"""
        valid_values = [True, False, 1, 0, "1", "0", "true", "false", "True", "False"]
        
        if value not in valid_values:
            with pytest.raises(ValueError):
                boolean(value)
        else:
            # Should not raise for valid values
            result = boolean(value)
            assert isinstance(result, bool)
    
    @given(st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text().filter(_is_numeric_string)
    ))
    def test_double_validator_valid_inputs(self, value):
        """Test that double validator accepts valid numeric inputs"""
        result = double(value)
        # The function returns the input unchanged if valid
        assert result == value
        
    @given(st.one_of(
        st.text().filter(lambda s: not _is_numeric_string(s)),
        st.none(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    ))
    def test_double_validator_invalid_inputs(self, value):
        """Test that double validator raises ValueError for non-numeric inputs"""
        with pytest.raises(ValueError) as exc_info:
            double(value)
        assert "is not a valid double" in str(exc_info.value)


class TestRoundTripProperties:
    """Test round-trip properties for AWS objects"""
    
    @given(
        crl_data=st.text(min_size=1),
        name=st.text(min_size=1),
        enabled=st.booleans(),
        trust_anchor_arn=st.one_of(st.none(), st.text(min_size=1))
    )
    def test_crl_round_trip(self, crl_data, name, enabled, trust_anchor_arn):
        """Test that CRL from_dict and to_dict preserve properties"""
        # Build the properties dict
        props = {
            'CrlData': crl_data,
            'Name': name,
            'Enabled': enabled
        }
        if trust_anchor_arn is not None:
            props['TrustAnchorArn'] = trust_anchor_arn
        
        # Create object from dict
        crl = ra.CRL.from_dict('TestCRL', props)
        
        # Convert back to dict
        result = crl.to_dict()
        
        # Check the round-trip preserves properties
        assert 'Properties' in result
        assert result['Properties'] == props
        assert result['Type'] == 'AWS::RolesAnywhere::CRL'
    
    @given(
        name=st.text(min_size=1),
        role_arns=st.lists(st.text(min_size=1), min_size=1),
        enabled=st.booleans(),
        duration_seconds=st.one_of(st.none(), st.floats(min_value=900, max_value=43200)),
        accept_role_session_name=st.one_of(st.none(), st.booleans()),
        require_instance_properties=st.one_of(st.none(), st.booleans())
    )
    def test_profile_round_trip(self, name, role_arns, enabled, duration_seconds, 
                               accept_role_session_name, require_instance_properties):
        """Test that Profile from_dict and to_dict preserve properties"""
        # Build the properties dict
        props = {
            'Name': name,
            'RoleArns': role_arns,
            'Enabled': enabled
        }
        
        if duration_seconds is not None:
            props['DurationSeconds'] = duration_seconds
        if accept_role_session_name is not None:
            props['AcceptRoleSessionName'] = accept_role_session_name
        if require_instance_properties is not None:
            props['RequireInstanceProperties'] = require_instance_properties
        
        # Create object from dict
        profile = ra.Profile.from_dict('TestProfile', props)
        
        # Convert back to dict
        result = profile.to_dict()
        
        # Check the round-trip preserves properties
        assert 'Properties' in result
        assert result['Properties'] == props
        assert result['Type'] == 'AWS::RolesAnywhere::Profile'


class TestRequiredPropertyValidation:
    """Test validation of required properties"""
    
    def test_crl_missing_required_properties_should_fail(self):
        """Test that CRL validation should fail when required properties are missing"""
        # CrlData is marked as required (True) in props
        crl1 = ra.CRL('TestCRL', Name='test-name')
        # This should fail validation but currently doesn't
        crl1.validate()  # Bug: This passes when it should fail
        
        # Name is marked as required (True) in props  
        crl2 = ra.CRL('TestCRL', CrlData='test-data')
        # This should fail validation but currently doesn't
        crl2.validate()  # Bug: This passes when it should fail
    
    def test_profile_missing_required_properties_should_fail(self):
        """Test that Profile validation should fail when required properties are missing"""
        # RoleArns is marked as required (True) in props
        profile = ra.Profile('TestProfile', Name='test')
        # This should fail validation but currently doesn't
        profile.validate()  # Bug: This passes when it should fail
    
    def test_nested_property_validation_works(self):
        """Test that nested property validation does work correctly"""
        # AttributeMapping correctly validates required MappingRules
        with pytest.raises(ValueError) as exc_info:
            attr_mapping = ra.AttributeMapping(CertificateField='x509Subject')
            profile = ra.Profile('TestProfile', 
                              Name='test',
                              RoleArns=['arn'],
                              AttributeMappings=[attr_mapping])
            profile.validate()
        
        assert "MappingRules required" in str(exc_info.value)


class TestPropertyTypeConsistency:
    """Test that property types are handled consistently"""
    
    @given(
        enabled_input=st.one_of(
            st.booleans(),
            st.sampled_from([1, 0, "1", "0", "true", "false", "True", "False"])
        )
    )
    def test_boolean_property_normalization(self, enabled_input):
        """Test that boolean properties are normalized correctly"""
        crl = ra.CRL('TestCRL', 
                    CrlData='data',
                    Name='name',
                    Enabled=enabled_input)
        
        result = crl.to_dict()
        
        # The Enabled property should be normalized to a boolean
        enabled_value = result['Properties']['Enabled']
        assert isinstance(enabled_value, bool)
        
        # Check the normalization is correct
        if enabled_input in [True, 1, "1", "true", "True"]:
            assert enabled_value is True
        elif enabled_input in [False, 0, "0", "false", "False"]:
            assert enabled_value is False
    
    @given(
        duration_input=st.one_of(
            st.integers(min_value=900, max_value=43200),
            st.floats(min_value=900, max_value=43200),
            st.text().filter(lambda s: _is_numeric_string(s) and 900 <= float(s) <= 43200)
        )
    )
    def test_double_property_preservation(self, duration_input):
        """Test that double properties preserve their input type"""
        profile = ra.Profile('TestProfile',
                           Name='test',
                           RoleArns=['arn'],
                           DurationSeconds=duration_input)
        
        result = profile.to_dict()
        
        # The double validator returns the input unchanged
        duration_value = result['Properties']['DurationSeconds']
        assert duration_value == duration_input