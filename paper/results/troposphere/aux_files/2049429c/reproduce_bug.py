from troposphere.s3objectlambda import AccessPoint, AccessPointPolicy, ObjectLambdaConfiguration, TransformationConfiguration, ContentTransformation, AwsLambda

# Minimal reproduction of the bug

# Test 1: AccessPointPolicy without title
print("Test 1: AccessPointPolicy without positional title argument")
try:
    policy = AccessPointPolicy(
        ObjectLambdaAccessPoint="test-ap",
        PolicyDocument={"Version": "2012-10-17"}
    )
    print("SUCCESS: Created without title")
except TypeError as e:
    print(f"FAILED: {e}")

# Test 2: AccessPointPolicy with title as keyword argument  
print("\nTest 2: AccessPointPolicy with title as keyword argument")
try:
    policy = AccessPointPolicy(
        title="MyPolicy",
        ObjectLambdaAccessPoint="test-ap",
        PolicyDocument={"Version": "2012-10-17"}
    )
    print("SUCCESS: Created with title as keyword")
except TypeError as e:
    print(f"FAILED: {e}")

# Test 3: AccessPointPolicy with title as positional argument
print("\nTest 3: AccessPointPolicy with title as positional argument")
try:
    policy = AccessPointPolicy(
        "MyPolicy",
        ObjectLambdaAccessPoint="test-ap",
        PolicyDocument={"Version": "2012-10-17"}
    )
    print("SUCCESS: Created with title as positional")
    print(f"Policy title: {policy.title}")
    print(f"Policy to_dict: {policy.to_dict()}")
except Exception as e:
    print(f"FAILED: {e}")

# Test 4: AccessPoint without title
print("\nTest 4: AccessPoint without positional title argument")
try:
    aws_lambda = AwsLambda(FunctionArn="arn:aws:lambda:us-east-1:123456789012:function:MyFunction")
    content = ContentTransformation(AwsLambda=aws_lambda)
    transform = TransformationConfiguration(
        Actions=["GetObject"],
        ContentTransformation=content
    )
    obj_lambda = ObjectLambdaConfiguration(
        SupportingAccessPoint="my-s3-ap",
        TransformationConfigurations=[transform]
    )
    
    ap = AccessPoint(
        ObjectLambdaConfiguration=obj_lambda
    )
    print("SUCCESS: Created without title")
except TypeError as e:
    print(f"FAILED: {e}")

# Test 5: AccessPoint with None title
print("\nTest 5: AccessPoint with None as title")
try:
    aws_lambda = AwsLambda(FunctionArn="arn:aws:lambda:us-east-1:123456789012:function:MyFunction")
    content = ContentTransformation(AwsLambda=aws_lambda)
    transform = TransformationConfiguration(
        Actions=["GetObject"],
        ContentTransformation=content
    )
    obj_lambda = ObjectLambdaConfiguration(
        SupportingAccessPoint="my-s3-ap",
        TransformationConfigurations=[transform]
    )
    
    ap = AccessPoint(
        None,  # Explicitly passing None as title
        ObjectLambdaConfiguration=obj_lambda
    )
    print("SUCCESS: Created with None title")
    print(f"AccessPoint title: {ap.title}")
except Exception as e:
    print(f"FAILED: {e}")

# Test 6: AccessPoint with empty string title
print("\nTest 6: AccessPoint with empty string as title")
try:
    aws_lambda = AwsLambda(FunctionArn="arn:aws:lambda:us-east-1:123456789012:function:MyFunction")
    content = ContentTransformation(AwsLambda=aws_lambda)
    transform = TransformationConfiguration(
        Actions=["GetObject"],
        ContentTransformation=content
    )
    obj_lambda = ObjectLambdaConfiguration(
        SupportingAccessPoint="my-s3-ap",
        TransformationConfigurations=[transform]
    )
    
    ap = AccessPoint(
        "",  # Empty string as title
        ObjectLambdaConfiguration=obj_lambda
    )
    print("SUCCESS: Created with empty string title")
    ap.to_dict()  # Try to validate
    print("Validated successfully")
except Exception as e:
    print(f"FAILED during validation: {e}")