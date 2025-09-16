#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.arczonalshift import ZonalAutoshiftConfiguration

# This should work since PracticeRunConfiguration is optional (False in props)
# but it raises a TypeError
config = ZonalAutoshiftConfiguration(
    "TestConfig",
    ResourceIdentifier="test-resource",
    PracticeRunConfiguration=None
)

print("Success - None value accepted for optional property")