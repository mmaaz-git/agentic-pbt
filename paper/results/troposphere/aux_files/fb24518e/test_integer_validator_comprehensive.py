#!/usr/bin/env python3
"""
Comprehensive test showing the integer validator bug affects all integer properties.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.greengrass as greengrass

# Test different resources with integer properties

# 1. Logger with Space property (integer)
logger = greengrass.Logger(
    "TestLogger",
    Component="test",
    Id="logger-id",
    Level="INFO",
    Type="FileSystem",
    Space=100.0  # Float instead of int
)

logger_dict = logger.to_dict()
print(f"Logger.Space: {logger_dict.get('Space')} (type: {type(logger_dict.get('Space')).__name__})")
assert logger_dict.get('Space') == 100.0
assert isinstance(logger_dict.get('Space'), float), "Bug: Should have been converted to int"

# 2. FunctionConfiguration with MemorySize and Timeout (integer)
func_config = greengrass.FunctionConfiguration(
    "TestFuncConfig",
    MemorySize=256.0,  # Float instead of int
    Timeout=30.0       # Float instead of int
)

func_dict = func_config.to_dict()
print(f"FunctionConfiguration.MemorySize: {func_dict.get('MemorySize')} (type: {type(func_dict.get('MemorySize')).__name__})")
print(f"FunctionConfiguration.Timeout: {func_dict.get('Timeout')} (type: {type(func_dict.get('Timeout')).__name__})")
assert isinstance(func_dict.get('MemorySize'), float), "Bug: Should have been converted to int"
assert isinstance(func_dict.get('Timeout'), float), "Bug: Should have been converted to int"

# 3. RunAs with Gid and Uid (integer)
run_as = greengrass.RunAs(
    "TestRunAs",
    Gid=1000.0,  # Float instead of int
    Uid=1000.0   # Float instead of int
)

run_as_dict = run_as.to_dict()
print(f"RunAs.Gid: {run_as_dict.get('Gid')} (type: {type(run_as_dict.get('Gid')).__name__})")
print(f"RunAs.Uid: {run_as_dict.get('Uid')} (type: {type(run_as_dict.get('Uid')).__name__})")
assert isinstance(run_as_dict.get('Gid'), float), "Bug: Should have been converted to int"
assert isinstance(run_as_dict.get('Uid'), float), "Bug: Should have been converted to int"

print("\nBug affects all integer properties in troposphere.greengrass module!")
print("Float values are accepted but not converted to integers as expected.")