#!/usr/bin/env python3
"""Test if the round-trip bug exists in other troposphere modules"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Test with different troposphere modules
from troposphere import s3, ec2, iam

def test_aws_object_roundtrip(cls, title, **required_props):
    """Test if AWSObject subclass has round-trip bug"""
    try:
        obj = cls(title, **required_props)
        dict_repr = obj.to_dict()
        
        # This should work but likely won't
        try:
            reconstructed = cls.from_dict(title, dict_repr)
            return f"{cls.__name__}: OK - No bug"
        except AttributeError as e:
            if "Properties property" in str(e):
                # Try the workaround
                if 'Properties' in dict_repr:
                    reconstructed = cls.from_dict(title, dict_repr['Properties'])
                    return f"{cls.__name__}: BUG CONFIRMED - from_dict expects unwrapped dict"
            raise
    except Exception as e:
        return f"{cls.__name__}: Could not test - {e}"

# Test S3 Bucket (AWSObject)
print(test_aws_object_roundtrip(s3.Bucket, 'TestBucket'))

# Test EC2 Instance (AWSObject) - needs ImageId
print(test_aws_object_roundtrip(ec2.Instance, 'TestInstance', ImageId='ami-12345'))

# Test IAM Role (AWSObject) - needs AssumeRolePolicyDocument
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ec2.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}
print(test_aws_object_roundtrip(iam.Role, 'TestRole', 
                                AssumeRolePolicyDocument=assume_role_policy))