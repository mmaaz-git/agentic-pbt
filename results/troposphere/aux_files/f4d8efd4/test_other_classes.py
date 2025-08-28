import troposphere.efs as efs

# Test other AWS objects for the same issue
classes_to_test = [
    (efs.AccessPoint, "TestAP", {"FileSystemId": "fs-12345"}),
    (efs.MountTarget, "TestMT", {"FileSystemId": "fs-12345", "SecurityGroups": ["sg-123"], "SubnetId": "subnet-123"})
]

for cls, title, required_props in classes_to_test:
    print(f"\nTesting {cls.__name__}:")
    obj = cls(title=title, **required_props)
    dict_repr = obj.to_dict()
    print(f"  to_dict() keys: {list(dict_repr.keys())}")
    
    try:
        recovered = cls.from_dict(title, dict_repr)
        print(f"  ✓ Round-trip successful")
    except AttributeError as e:
        print(f"  ✗ Bug: {e}")