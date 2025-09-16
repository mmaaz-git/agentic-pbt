#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, find, example
from google.rpc import status_pb2
import grpc
from grpc_status import rpc_status
from grpc_status._common import code_to_grpc_status_code, GRPC_DETAILS_METADATA_KEY
from unittest.mock import Mock
import traceback

print("Testing grpc_status module properties...")
print("=" * 60)

# Test 1: Check edge cases for code_to_grpc_status_code
print("\nTest 1: code_to_grpc_status_code edge cases")
print("-" * 40)

# Check negative codes
try:
    result = code_to_grpc_status_code(-1)
    print(f"ERROR: Accepted negative code -1, got {result}")
except ValueError as e:
    print(f"✓ Correctly rejected negative code: {e}")

# Check large invalid codes
try:
    result = code_to_grpc_status_code(999)
    print(f"ERROR: Accepted invalid code 999, got {result}")
except ValueError as e:
    print(f"✓ Correctly rejected large invalid code: {e}")

# Check valid codes
valid_codes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
for code in valid_codes:
    try:
        result = code_to_grpc_status_code(code)
        assert result.value[0] == code
        print(f"✓ Code {code} maps to {result.name}")
    except Exception as e:
        print(f"ERROR: Failed on valid code {code}: {e}")

# Test 2: Check to_status with edge cases
print("\n\nTest 2: to_status edge cases")
print("-" * 40)

# Test with empty message
proto_status = status_pb2.Status()
proto_status.code = 0
proto_status.message = ""

try:
    grpc_status = rpc_status.to_status(proto_status)
    assert grpc_status.details == ""
    print("✓ Handles empty message correctly")
except Exception as e:
    print(f"ERROR: Failed with empty message: {e}")
    traceback.print_exc()

# Test with unicode in message
proto_status = status_pb2.Status()
proto_status.code = 1
proto_status.message = "Error: 🦄 Unicode test ñ é"

try:
    grpc_status = rpc_status.to_status(proto_status)
    assert grpc_status.details == "Error: 🦄 Unicode test ñ é"
    # Verify round-trip
    serialized = grpc_status.trailing_metadata[0][1]
    recovered = status_pb2.Status.FromString(serialized)
    assert recovered.message == proto_status.message
    print("✓ Handles unicode in messages correctly")
except Exception as e:
    print(f"ERROR: Failed with unicode message: {e}")
    traceback.print_exc()

# Test with very long message
proto_status = status_pb2.Status()
proto_status.code = 2
proto_status.message = "A" * 10000

try:
    grpc_status = rpc_status.to_status(proto_status)
    assert grpc_status.details == "A" * 10000
    print("✓ Handles long messages correctly")
except Exception as e:
    print(f"ERROR: Failed with long message: {e}")
    traceback.print_exc()

# Test 3: from_call validation
print("\n\nTest 3: from_call validation logic")
print("-" * 40)

# Test mismatched code
mock_call = Mock()
mock_call.code.return_value = Mock(value=(5, ""))  # GRPC code 5
mock_call.details.return_value = "Error message"

# Create a Status proto with different code
proto = status_pb2.Status()
proto.code = 3  # Different code
proto.message = "Error message"  # Same message

mock_call.trailing_metadata.return_value = [
    (GRPC_DETAILS_METADATA_KEY, proto.SerializeToString())
]

try:
    result = rpc_status.from_call(mock_call)
    print(f"ERROR: Should have raised ValueError for mismatched codes, got {result}")
except ValueError as e:
    print(f"✓ Correctly detected code mismatch: {e}")

# Test mismatched message
mock_call.code.return_value = Mock(value=(3, ""))  # Match the proto code now
mock_call.details.return_value = "Different message"  # Different message

try:
    result = rpc_status.from_call(mock_call)
    print(f"ERROR: Should have raised ValueError for mismatched messages, got {result}")
except ValueError as e:
    print(f"✓ Correctly detected message mismatch: {e}")

# Test 4: Property-based test for round-trip
print("\n\nTest 4: Round-trip property test")
print("-" * 40)

def test_round_trip(code, message):
    # Create original Status
    original = status_pb2.Status()
    original.code = code
    original.message = message
    
    # Convert to grpc.Status
    grpc_status = rpc_status.to_status(original)
    
    # Extract and parse back
    serialized = grpc_status.trailing_metadata[0][1]
    recovered = status_pb2.Status.FromString(serialized)
    
    return recovered.code == original.code and recovered.message == original.message

# Test with various inputs
test_cases = [
    (0, ""),
    (1, "Simple error"),
    (16, "Last valid code"),
    (5, "Message with\nnewlines\nand\ttabs"),
    (10, "🦄 ñ é unicode"),
]

for code, msg in test_cases:
    try:
        assert test_round_trip(code, msg)
        print(f"✓ Round-trip successful for code={code}, message='{msg[:20]}...'")
    except Exception as e:
        print(f"ERROR: Round-trip failed for code={code}, message='{msg}': {e}")

# Test 5: Check for potential integer overflow or boundary issues
print("\n\nTest 5: Boundary and edge case testing")
print("-" * 40)

# Test boundary of valid codes
for code in [16, 17]:  # 16 is last valid, 17 should be invalid
    proto = status_pb2.Status()
    proto.code = code
    proto.message = "test"
    
    try:
        grpc_status = rpc_status.to_status(proto)
        if code <= 16:
            print(f"✓ Code {code} accepted as valid")
        else:
            print(f"ERROR: Code {code} should have been rejected")
    except ValueError as e:
        if code > 16:
            print(f"✓ Code {code} correctly rejected: {e}")
        else:
            print(f"ERROR: Code {code} should have been accepted: {e}")

print("\n" + "=" * 60)
print("Testing complete!")