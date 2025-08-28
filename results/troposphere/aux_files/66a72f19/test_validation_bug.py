"""
Comprehensive test demonstrating validation inconsistency bug in troposphere.rolesanywhere
"""

import troposphere.rolesanywhere as ra
import pytest


def test_validation_inconsistency_crl():
    """Demonstrate that validate() doesn't check required properties but to_dict() does"""
    
    # CRL has two required properties: CrlData and Name
    # Create CRL missing CrlData
    crl1 = ra.CRL('TestCRL', Name='test-name')
    
    # validate() should fail but doesn't
    crl1.validate()  # Passes (BUG!)
    
    # to_dict() correctly fails
    with pytest.raises(ValueError) as exc:
        crl1.to_dict()
    assert "CrlData required" in str(exc.value)
    
    # Create CRL missing Name
    crl2 = ra.CRL('TestCRL', CrlData='test-data')
    
    # validate() should fail but doesn't
    crl2.validate()  # Passes (BUG!)
    
    # to_dict() correctly fails
    with pytest.raises(ValueError) as exc:
        crl2.to_dict()
    assert "Name required" in str(exc.value)
    
    # Create CRL with no properties at all
    crl3 = ra.CRL('TestCRL')
    
    # validate() should fail but doesn't
    crl3.validate()  # Passes (BUG!)
    
    # to_dict() correctly fails
    with pytest.raises(ValueError) as exc:
        crl3.to_dict()
    # Will fail on first missing required property
    assert "required" in str(exc.value)


def test_validation_inconsistency_profile():
    """Same bug affects Profile class"""
    
    # Profile requires Name and RoleArns
    # Create Profile missing RoleArns
    profile1 = ra.Profile('TestProfile', Name='test')
    
    # validate() should fail but doesn't
    profile1.validate()  # Passes (BUG!)
    
    # to_dict() correctly fails
    with pytest.raises(ValueError) as exc:
        profile1.to_dict()
    assert "RoleArns required" in str(exc.value)
    
    # Create Profile missing Name
    profile2 = ra.Profile('TestProfile', RoleArns=['arn:aws:iam::123456789012:role/test'])
    
    # validate() should fail but doesn't
    profile2.validate()  # Passes (BUG!)
    
    # to_dict() correctly fails
    with pytest.raises(ValueError) as exc:
        profile2.to_dict()
    assert "Name required" in str(exc.value)


def test_validation_inconsistency_trust_anchor():
    """Same bug affects TrustAnchor class"""
    
    # TrustAnchor requires Name and Source
    trust_anchor = ra.TrustAnchor('TestAnchor', Name='test')
    
    # validate() should fail but doesn't
    trust_anchor.validate()  # Passes (BUG!)
    
    # to_dict() correctly fails
    with pytest.raises(ValueError) as exc:
        trust_anchor.to_dict()
    assert "Source required" in str(exc.value)


def test_working_validation_when_properties_present():
    """Verify that objects work correctly when all required properties are present"""
    
    # CRL with all required properties
    crl = ra.CRL('TestCRL', CrlData='data', Name='name')
    crl.validate()  # Should pass
    result = crl.to_dict()  # Should also pass
    assert result['Properties']['CrlData'] == 'data'
    assert result['Properties']['Name'] == 'name'
    
    # Profile with all required properties
    profile = ra.Profile('TestProfile', Name='test', RoleArns=['arn'])
    profile.validate()  # Should pass
    result = profile.to_dict()  # Should also pass
    assert result['Properties']['Name'] == 'test'
    assert result['Properties']['RoleArns'] == ['arn']


if __name__ == "__main__":
    print("Running validation inconsistency tests...")
    
    # Run each test and show results
    tests = [
        test_validation_inconsistency_crl,
        test_validation_inconsistency_profile,
        test_validation_inconsistency_trust_anchor,
        test_working_validation_when_properties_present
    ]
    
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__} passed")
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")