import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.codestarconnections as csc

print("Test 1: Creating Connection without optional HostArn (should work):")
try:
    conn1 = csc.Connection(
        title="Test1",
        ConnectionName="MyConnection"
    )
    print("✓ Success - Connection created without HostArn")
    print(f"  to_dict: {conn1.to_dict()}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\nTest 2: Creating Connection with HostArn=None (testing None handling):")
try:
    conn2 = csc.Connection(
        title="Test2",
        ConnectionName="MyConnection",
        HostArn=None  # Explicitly passing None for optional property
    )
    print("✓ Success - Connection created with HostArn=None")
    print(f"  to_dict: {conn2.to_dict()}")
except TypeError as e:
    print(f"✗ Failed with TypeError: {e}")
    print("  This means None is not accepted for optional properties")

print("\nTest 3: Creating Connection with empty string HostArn:")
try:
    conn3 = csc.Connection(
        title="Test3",
        ConnectionName="MyConnection",
        HostArn=""  # Empty string instead of None
    )
    print("✓ Success - Connection created with HostArn=''")
    print(f"  to_dict: {conn3.to_dict()}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\nAnalysis:")
print("- Optional properties can be omitted (Test 1: ✓)")
print("- Optional properties CANNOT be explicitly set to None (Test 2: ✗)")
print("- Optional properties CAN be set to empty string (Test 3: ✓)")
print("\nThis is arguably a bug because:")
print("1. In Python, None is the standard way to represent 'no value'")
print("2. Many APIs/libraries allow None for optional parameters")
print("3. Users might expect conn(HostArn=None) == conn() for optional props")