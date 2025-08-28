import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.athena import CapacityReservation, WorkGroupConfiguration

print("Testing CapacityReservation.TargetDpus (should be integer):")
cr = CapacityReservation("TestReservation", Name="test", TargetDpus=10.5)
print(f"  TargetDpus=10.5 -> {cr.TargetDpus}")

print("\nTesting WorkGroupConfiguration.BytesScannedCutoffPerQuery (should be integer):")
wgc = WorkGroupConfiguration(BytesScannedCutoffPerQuery=1000.7)
print(f"  BytesScannedCutoffPerQuery=1000.7 -> {wgc.BytesScannedCutoffPerQuery}")

print("\nIn AWS CloudFormation, integer properties should not accept float values.")
print("This could lead to unexpected behavior when deploying to AWS.")