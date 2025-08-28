"""
Test if the None handling bug affects other classes with optional fields
"""

import troposphere.route53 as r53

print("Testing None handling for optional fields across multiple classes")
print("=" * 70)

# Test classes with optional fields
test_cases = [
    # (Class, required_fields, optional_field_name)
    (r53.RecordSet, {'Name': 'test.com', 'Type': 'A'}, 'TTL'),
    (r53.RecordSet, {'Name': 'test.com', 'Type': 'A'}, 'HealthCheckId'),
    (r53.GeoLocation, {}, 'CountryCode'),
    (r53.AliasTarget, {'hostedzoneid': 'Z123', 'dnsname': 'example.com'}, 'evaluatetargethealth'),
]

bugs_found = []

for cls, required_fields, optional_field in test_cases:
    print(f"\nTesting {cls.__name__}.{optional_field}:")
    
    # Test 1: Omitting optional field
    try:
        obj1 = cls(**required_fields)
        print(f"  ✓ Omitting {optional_field}: SUCCESS")
    except Exception as e:
        print(f"  ✗ Omitting {optional_field}: {e}")
    
    # Test 2: Passing None explicitly
    fields_with_none = {**required_fields, optional_field: None}
    try:
        obj2 = cls(**fields_with_none)
        print(f"  ✓ {optional_field}=None: SUCCESS")
    except TypeError as e:
        print(f"  ✗ {optional_field}=None: {e}")
        bugs_found.append((cls.__name__, optional_field))

print("\n" + "=" * 70)
if bugs_found:
    print(f"BUGS FOUND: {len(bugs_found)} classes reject None for optional fields:")
    for class_name, field in bugs_found:
        print(f"  - {class_name}.{field}")
else:
    print("No additional bugs found in tested classes")