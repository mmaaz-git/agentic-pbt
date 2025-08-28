"""Specific test to demonstrate the JSON serialization bug with Default values"""

import pytest
from aiogram.methods import SendMessage
from aiogram.client.default import Default


def test_default_values_prevent_json_serialization():
    """Demonstrate that Default values prevent JSON serialization"""
    
    # Create a SendMessage with minimal required fields
    msg = SendMessage(chat_id=123456789, text="Hello World")
    
    # Check that Default objects are present in the dumped data
    dumped = msg.model_dump()
    print("\nDumped data contains these Default fields:")
    for key, value in dumped.items():
        if isinstance(value, Default):
            print(f"  {key}: {value}")
    
    # Verify Default objects are present
    has_defaults = any(isinstance(v, Default) for v in dumped.values())
    assert has_defaults, "Expected Default objects in model_dump() output"
    
    # Try to serialize to JSON - this should fail
    try:
        json_str = msg.model_dump_json()
        print(f"\nUnexpectedly succeeded! JSON: {json_str}")
        assert False, "Expected serialization to fail with Default objects"
    except Exception as e:
        print(f"\nSerialization failed as expected:")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {str(e)}")
        
        # Verify the error is about serialization
        assert "serialize" in str(e).lower() or "Default" in str(e), \
            f"Expected serialization error, got: {e}"
        
        return e


def test_without_defaults_serialization_works():
    """Show that serialization works when we exclude Default values"""
    
    msg = SendMessage(chat_id=123456789, text="Hello World")
    
    # Dump excluding unset (which includes Default values)
    dumped = msg.model_dump(exclude_unset=True)
    print("\nDumped data (exclude_unset=True):")
    for key, value in dumped.items():
        print(f"  {key}: {value} (type: {type(value).__name__})")
    
    # Verify no Default objects remain
    has_defaults = any(isinstance(v, Default) for v in dumped.values())
    assert not has_defaults, "Should not have Default objects when exclude_unset=True"
    
    # Now JSON serialization should work
    json_str = msg.model_dump_json(exclude_unset=True)
    print(f"\nSuccessfully serialized to JSON: {json_str}")
    assert json_str
    assert "123456789" in json_str
    assert "Hello World" in json_str


if __name__ == "__main__":
    print("=" * 60)
    print("Testing JSON serialization bug with Default values")
    print("=" * 60)
    
    error = test_default_values_prevent_json_serialization()
    print("\n" + "=" * 60)
    test_without_defaults_serialization_works()
    
    print("\n" + "=" * 60)
    print("CONCLUSION: model_dump_json() fails with Default objects present")
    print("WORKAROUND: Use model_dump_json(exclude_unset=True)")
    print("=" * 60)