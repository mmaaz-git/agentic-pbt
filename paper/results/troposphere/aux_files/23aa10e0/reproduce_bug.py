import troposphere.resiliencehub as rh

# Create a valid ResiliencyPolicy with FailurePolicy objects
failure_policy = rh.FailurePolicy(RpoInSecs=60, RtoInSecs=120)
policy = rh.ResiliencyPolicy(
    'TestPolicy',
    PolicyName='MyPolicy',
    Tier='Critical',
    Policy={'Software': failure_policy}
)

# Serialize to dict
serialized = policy.to_dict()
print("Serialization successful")
print(f"Serialized Policy: {serialized['Properties']['Policy']}")

# Try to deserialize from dict - this should work but doesn't
try:
    reconstructed = rh.ResiliencyPolicy.from_dict('NewPolicy', serialized['Properties'])
    print("Deserialization successful")
except ValueError as e:
    print(f"Deserialization failed: {e}")
    print("BUG: Cannot round-trip ResiliencyPolicy through to_dict/from_dict")