#!/usr/bin/env python3
"""Comprehensive test showing deferred validation bug in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cloudtrail as cloudtrail

def test_class_with_required_props(cls_name, cls, required_props):
    """Test that a class properly validates required properties."""
    print(f"\nTesting {cls_name}:")
    
    # Test 1: Creating without any required properties
    try:
        # Check if it's an AWSObject (needs title) or AWSProperty (doesn't)
        if hasattr(cls, 'resource_type'):  # AWSObject
            obj = cls("TestObject")
        else:  # AWSProperty
            obj = cls()
        print(f"  ✗ Created {cls_name} without required properties")
        
        # Check if to_dict() catches it
        try:
            obj.to_dict()
            print(f"  ✗✗ to_dict() also succeeded - SEVERE BUG")
        except ValueError as e:
            print(f"  ✓ to_dict() caught the error: {str(e)[:60]}...")
            
    except ValueError as e:
        print(f"  ✓ Correctly raised error at creation: {str(e)[:60]}...")
        

# Test all classes with required properties in cloudtrail module
print("="*70)
print("Testing classes with required properties in troposphere.cloudtrail")
print("="*70)

# Destination requires Location and Type
test_class_with_required_props("Destination", cloudtrail.Destination, 
                              {"Location": "str", "Type": "str"})

# Frequency requires Unit and Value  
test_class_with_required_props("Frequency", cloudtrail.Frequency,
                              {"Unit": "str", "Value": "integer"})

# Widget requires QueryStatement
test_class_with_required_props("Widget", cloudtrail.Widget,
                              {"QueryStatement": "str"})

# Trail requires IsLogging and S3BucketName
test_class_with_required_props("Trail", cloudtrail.Trail,
                              {"IsLogging": "boolean", "S3BucketName": "str"})

# ResourcePolicy requires ResourceArn and ResourcePolicy
test_class_with_required_props("ResourcePolicy", cloudtrail.ResourcePolicy,
                              {"ResourceArn": "str", "ResourcePolicy": "dict"})

# AdvancedFieldSelector requires Field
test_class_with_required_props("AdvancedFieldSelector", cloudtrail.AdvancedFieldSelector,
                              {"Field": "str"})

# AdvancedEventSelector requires FieldSelectors
test_class_with_required_props("AdvancedEventSelector", cloudtrail.AdvancedEventSelector,
                              {"FieldSelectors": "list"})

# DataResource requires Type
test_class_with_required_props("DataResource", cloudtrail.DataResource,
                              {"Type": "str"})

print("\n" + "="*70)
print("SUMMARY: All classes allow creation without required properties!")
print("Validation is deferred until to_dict() is called.")
print("="*70)