#!/usr/bin/env python3
"""Verification script for django.urls.converters bug"""

from django.urls.converters import (
    StringConverter, IntConverter, SlugConverter, 
    PathConverter, UUIDConverter
)

def verify_bug():
    print("Testing django.urls.converters to_url() return types\n")
    print("=" * 60)
    
    converters = {
        'StringConverter': StringConverter(),
        'IntConverter': IntConverter(),
        'SlugConverter': SlugConverter(),
        'PathConverter': PathConverter(),
        'UUIDConverter': UUIDConverter(),
    }
    
    test_values = [42, True, 3.14, None]
    
    for conv_name, conv in converters.items():
        print(f"\n{conv_name}:")
        for value in test_values:
            try:
                result = conv.to_url(value)
                result_type = type(result).__name__
                is_string = isinstance(result, str)
                status = "✓" if is_string else "✗ BUG"
                print(f"  to_url({value!r:5}) -> {result!r:10} (type: {result_type:5}) {status}")
            except Exception as e:
                print(f"  to_url({value!r:5}) -> ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("\nSUMMARY:")
    print("✗ StringConverter, SlugConverter, PathConverter: Don't convert to string")
    print("✓ IntConverter, UUIDConverter: Correctly convert to string")

if __name__ == "__main__":
    verify_bug()