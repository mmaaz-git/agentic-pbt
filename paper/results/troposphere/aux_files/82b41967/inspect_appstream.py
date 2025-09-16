import inspect
from troposphere import appstream, BaseAWSObject, AWSProperty

# Look at some example classes
print("=== S3Location (AWSProperty) ===")
s3_loc = appstream.S3Location
print(f"Base classes: {s3_loc.__bases__}")
print(f"Methods: {[m for m in dir(s3_loc) if not m.startswith('_') and callable(getattr(s3_loc, m))]}")

print("\n=== AppBlock (AWSObject) ===")
app_block = appstream.AppBlock
print(f"Base classes: {app_block.__bases__}")
print(f"Methods: {[m for m in dir(app_block) if not m.startswith('_') and callable(getattr(app_block, m))]}")

# Try creating instances
print("\n=== Creating instances ===")
try:
    # Try creating an S3Location with required props
    s3 = appstream.S3Location(S3Bucket="mybucket", S3Key="mykey")
    print(f"S3Location created successfully")
    print(f"S3Location dict: {s3.to_dict()}")
except Exception as e:
    print(f"Error creating S3Location: {e}")

try:
    # Try creating an AppBlock with minimal required props
    ab = appstream.AppBlock(
        "MyAppBlock",
        Name="TestBlock",
        SourceS3Location=appstream.S3Location(S3Bucket="bucket", S3Key="key")
    )
    print(f"AppBlock created successfully")
    print(f"AppBlock title: {ab.title}")
    print(f"AppBlock resource_type: {ab.resource_type}")
except Exception as e:
    print(f"Error creating AppBlock: {e}")

# Check validation behavior
print("\n=== Validation behavior ===")
try:
    # Try with missing required field
    s3_bad = appstream.S3Location(S3Bucket="mybucket")  # Missing S3Key
    print("S3Location with missing required field created")
except Exception as e:
    print(f"Error with missing required field: {e}")

# Check props structure
print("\n=== Props structure ===")
print(f"S3Location.props: {appstream.S3Location.props}")
print(f"ComputeCapacity.props: {appstream.ComputeCapacity.props}")