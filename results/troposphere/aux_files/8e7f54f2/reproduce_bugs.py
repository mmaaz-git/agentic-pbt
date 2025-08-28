import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codecommit as codecommit

print("Bug 1: Empty string accepted as valid Repository title")
print("=" * 60)
try:
    # This should fail validation but doesn't
    repo = codecommit.Repository(
        "",  # Empty title should be invalid
        RepositoryName="TestRepo"
    )
    print("UNEXPECTED: Empty title was accepted!")
    print(f"Title: '{repo.title}'")
except ValueError as e:
    print(f"Expected error: {e}")

print("\n" + "=" * 60)
print("Bug 2: None not handled for optional string properties")
print("=" * 60)
try:
    # This should work - RepositoryDescription is optional
    repo = codecommit.Repository(
        "MyRepo",
        RepositoryName="TestRepo",
        RepositoryDescription=None  # Should be allowed for optional property
    )
    print("SUCCESS: None accepted for optional RepositoryDescription")
except TypeError as e:
    print(f"UNEXPECTED TypeError: {e}")

print("\n" + "=" * 60)
print("Bug 3: None not handled for optional list properties")
print("=" * 60)
try:
    # This should work - Branches is optional
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=["createReference"],
        Branches=None  # Should be allowed for optional property
    )
    print("SUCCESS: None accepted for optional Branches")
except TypeError as e:
    print(f"UNEXPECTED TypeError: {e}")

print("\n" + "=" * 60)
print("Bug 4: None not handled for optional CustomData")
print("=" * 60)
try:
    # This should work - CustomData is optional
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=["createReference"],
        CustomData=None  # Should be allowed for optional property
    )
    print("SUCCESS: None accepted for optional CustomData")
except TypeError as e:
    print(f"UNEXPECTED TypeError: {e}")

print("\n" + "=" * 60)
print("Additional test: What about empty string for optional properties?")
print("=" * 60)
try:
    # Empty string should work
    repo = codecommit.Repository(
        "MyRepo",
        RepositoryName="TestRepo",
        RepositoryDescription=""  # Empty string
    )
    print("SUCCESS: Empty string accepted for RepositoryDescription")
    print(f"Description: '{repo.RepositoryDescription}'")
except Exception as e:
    print(f"ERROR: {e}")

try:
    trigger = codecommit.Trigger(
        Name="TestTrigger",
        DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
        Events=["createReference"],
        CustomData=""  # Empty string
    )
    print("SUCCESS: Empty string accepted for CustomData")
    print(f"CustomData: '{trigger.CustomData}'")
except Exception as e:
    print(f"ERROR: {e}")