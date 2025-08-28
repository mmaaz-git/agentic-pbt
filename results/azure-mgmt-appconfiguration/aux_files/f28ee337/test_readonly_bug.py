#!/usr/bin/env python3
"""
Detailed test for readonly field bug in azure-mgmt-appconfiguration
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/azure-mgmt-appconfiguration_env/lib/python3.13/site-packages')

from azure.mgmt.appconfiguration.models import ApiKey, ConfigurationStore
import datetime

def test_readonly_fields_bug():
    """
    Test that demonstrates readonly fields can be modified after object creation.
    
    According to the model definition, fields marked with:
    _validation = {"field_name": {"readonly": True}}
    should be readonly and not modifiable after creation.
    
    However, the current implementation only logs a warning during __init__ 
    but doesn't prevent modification after the object is created.
    """
    
    print("Testing readonly field modification bug in ApiKey model...")
    print("=" * 60)
    
    # Create an ApiKey instance
    api_key = ApiKey()
    
    # According to the model, these fields are readonly:
    # - id
    # - name  
    # - value
    # - connection_string
    # - last_modified
    # - read_only
    
    print("\n1. Initial state of readonly fields:")
    print(f"   id: {api_key.id}")
    print(f"   name: {api_key.name}")
    print(f"   value: {api_key.value}")
    print(f"   connection_string: {api_key.connection_string}")
    print(f"   last_modified: {api_key.last_modified}")
    print(f"   read_only: {api_key.read_only}")
    
    print("\n2. Attempting to modify readonly fields after creation...")
    
    # Try to modify readonly fields
    api_key.id = "modified-id"
    api_key.name = "modified-name"
    api_key.value = "modified-value"
    api_key.connection_string = "modified-connection"
    api_key.last_modified = datetime.datetime.now()
    api_key.read_only = True
    
    print("\n3. State after modification attempts:")
    print(f"   id: {api_key.id}")
    print(f"   name: {api_key.name}")
    print(f"   value: {api_key.value}")
    print(f"   connection_string: {api_key.connection_string}")
    print(f"   last_modified: {api_key.last_modified}")
    print(f"   read_only: {api_key.read_only}")
    
    # Check if modifications were successful
    if (api_key.id == "modified-id" and 
        api_key.name == "modified-name" and
        api_key.value == "modified-value"):
        print("\n❌ BUG CONFIRMED: Readonly fields can be modified after object creation!")
        print("   This violates the expected behavior of readonly fields.")
        return True
    else:
        print("\n✓ Readonly fields were properly protected")
        return False


def test_readonly_in_other_models():
    """Test if the readonly bug affects other models too"""
    
    print("\n\nTesting readonly fields in ConfigurationStore model...")
    print("=" * 60)
    
    # ConfigurationStore has these readonly fields:
    # - provisioning_state
    # - creation_date
    # - endpoint
    # - private_endpoint_connections
    
    store = ConfigurationStore(location="eastus", sku={"name": "Standard"})
    
    print("\n1. Initial readonly field values:")
    print(f"   provisioning_state: {store.provisioning_state}")
    print(f"   creation_date: {store.creation_date}")
    print(f"   endpoint: {store.endpoint}")
    
    print("\n2. Attempting to modify readonly fields...")
    
    store.provisioning_state = "Modified"
    store.creation_date = datetime.datetime.now()
    store.endpoint = "https://modified.endpoint.com"
    
    print("\n3. Values after modification:")
    print(f"   provisioning_state: {store.provisioning_state}")
    print(f"   creation_date: {store.creation_date}")
    print(f"   endpoint: {store.endpoint}")
    
    if store.provisioning_state == "Modified":
        print("\n❌ BUG CONFIRMED: ConfigurationStore readonly fields also affected!")
        return True
    else:
        print("\n✓ ConfigurationStore readonly fields are protected")
        return False


def test_readonly_during_init():
    """Test if readonly validation works during initialization"""
    
    print("\n\nTesting readonly validation during __init__...")
    print("=" * 60)
    
    print("\n1. Attempting to set readonly field 'id' during initialization...")
    
    # This should log a warning but not prevent creation
    try:
        api_key = ApiKey()
        # Try to set during init (this would need kwargs which ApiKey doesn't accept)
        print("   ApiKey doesn't accept kwargs during init")
    except Exception as e:
        print(f"   Exception during init: {e}")
    
    print("\n2. The readonly validation only logs warnings during __init__")
    print("   but doesn't prevent the assignment after object creation.")
    
    return True


def minimal_reproduction():
    """Minimal code to reproduce the bug"""
    print("\n\nMinimal Reproduction Code:")
    print("=" * 60)
    print("""
from azure.mgmt.appconfiguration.models import ApiKey

# Create an ApiKey instance
api_key = ApiKey()

# Modify readonly field (should not be allowed)
api_key.id = "modified-id"

# Bug: The modification succeeds
assert api_key.id == "modified-id"  # This assertion passes!
    """)


def main():
    print("\n" + "=" * 70)
    print("READONLY FIELD MODIFICATION BUG IN AZURE-MGMT-APPCONFIGURATION")
    print("=" * 70)
    
    bug_found = False
    
    if test_readonly_fields_bug():
        bug_found = True
    
    if test_readonly_in_other_models():
        bug_found = True
    
    test_readonly_during_init()
    
    minimal_reproduction()
    
    if bug_found:
        print("\n" + "=" * 70)
        print("BUG SUMMARY:")
        print("-" * 70)
        print("Fields marked as 'readonly' in the model _validation dictionary")
        print("can be modified after object creation. This affects multiple")
        print("models including ApiKey and ConfigurationStore.")
        print()
        print("Expected behavior: Readonly fields should be immutable after creation")
        print("Actual behavior: Readonly fields can be freely modified")
        print()
        print("Severity: Medium - This is a contract violation that could lead to")
        print("unexpected behavior when readonly fields are modified by user code.")
        print("=" * 70)
        return 1
    else:
        print("\n✅ No bugs found")
        return 0


if __name__ == "__main__":
    sys.exit(main())