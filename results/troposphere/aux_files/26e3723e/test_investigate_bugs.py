"""Investigate potential bugs found in edge case testing."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import certificatemanager


def test_empty_title_bug():
    """Investigate empty title handling."""
    try:
        cert = certificatemanager.Certificate(
            title="",
            DomainName="example.com"
        )
        print(f"Empty title accepted: cert.title = '{cert.title}'")
        print(f"Title validation passed for empty string")
        
        # Try to serialize
        dict_repr = cert.to_dict()
        print(f"Serialization successful with empty title")
        print(f"Dict repr: {dict_repr}")
    except ValueError as e:
        print(f"ValueError raised: {e}")
    except Exception as e:
        print(f"Other exception: {type(e).__name__}: {e}")


def test_float_integer_bug():
    """Investigate float handling in integer fields."""
    try:
        # Test with float
        config = certificatemanager.ExpiryEventsConfiguration(
            DaysBeforeExpiry=3.14
        )
        print(f"Float value accepted: DaysBeforeExpiry = {config.properties.get('DaysBeforeExpiry', 'NOT SET')}")
        
        account = certificatemanager.Account(
            title="TestAccount",
            ExpiryEventsConfiguration=config
        )
        
        # Try to serialize
        dict_repr = account.to_dict()
        print(f"Serialization successful with float value")
        print(f"Dict repr DaysBeforeExpiry: {dict_repr['Properties']['ExpiryEventsConfiguration']['DaysBeforeExpiry']}")
        print(f"Type of DaysBeforeExpiry: {type(dict_repr['Properties']['ExpiryEventsConfiguration']['DaysBeforeExpiry'])}")
    except ValueError as e:
        print(f"ValueError raised: {e}")
    except TypeError as e:
        print(f"TypeError raised: {e}")
    except Exception as e:
        print(f"Other exception: {type(e).__name__}: {e}")


def test_validation_mechanism():
    """Test when validation actually happens."""
    print("\n=== Testing validation mechanism ===")
    
    # Create certificate without required field
    cert = certificatemanager.Certificate(title="Test")
    print(f"Certificate created without DomainName")
    
    # Check if properties are set
    print(f"Properties: {cert.properties}")
    
    # Try to access to_dict without validation
    try:
        dict_repr = cert.to_dict(validation=False)
        print(f"to_dict(validation=False) succeeded: {dict_repr}")
    except Exception as e:
        print(f"to_dict(validation=False) failed: {e}")
    
    # Try with validation
    try:
        dict_repr = cert.to_dict(validation=True)
        print(f"to_dict(validation=True) succeeded: {dict_repr}")
    except Exception as e:
        print(f"to_dict(validation=True) failed: {e}")


if __name__ == "__main__":
    test_empty_title_bug()
    print("\n" + "="*50 + "\n")
    test_float_integer_bug()
    print("\n" + "="*50 + "\n")
    test_validation_mechanism()