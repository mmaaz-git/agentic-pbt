#!/usr/bin/env python3
"""Investigate the microseconds round-trip bug."""

import datetime
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

from google.api_core import datetime_helpers

# Test case from the failure
dt = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)
print(f"Original datetime: {dt}")
print(f"Original datetime tzinfo: {dt.tzinfo}")

micros = datetime_helpers.to_microseconds(dt)
print(f"Microseconds: {micros}")

dt_reconstructed = datetime_helpers.from_microseconds(micros)
print(f"Reconstructed datetime: {dt_reconstructed}")
print(f"Reconstructed datetime tzinfo: {dt_reconstructed.tzinfo}")

# The issue is that from_microseconds returns UTC datetime but the comparison is wrong
# Let me check the actual implementation more carefully

# Test with a non-epoch datetime
dt2 = datetime.datetime(2024, 6, 15, 14, 30, 45, 123456, tzinfo=datetime.timezone.utc)
print(f"\nOriginal datetime 2: {dt2}")

micros2 = datetime_helpers.to_microseconds(dt2)
print(f"Microseconds 2: {micros2}")

dt2_reconstructed = datetime_helpers.from_microseconds(micros2)
print(f"Reconstructed datetime 2: {dt2_reconstructed}")
print(f"Reconstructed datetime 2 tzinfo: {dt2_reconstructed.tzinfo}")

# Check if they're actually equal when accounting for timezone
if dt2.replace(tzinfo=None) == dt2_reconstructed.replace(tzinfo=None):
    print("Values are equal when timezone is ignored")
else:
    print("Values differ even without timezone!")
    
# Actually, let me check if from_microseconds always returns UTC
print(f"\nChecking from_microseconds return value:")
print(f"Type: {type(dt2_reconstructed)}")
print(f"Timezone: {dt2_reconstructed.tzinfo}")

# Looking at the code, from_microseconds returns a UTC datetime WITH timezone info
# Let's verify this
test_micros = 1718461845123456  # Some arbitrary microseconds
test_dt = datetime_helpers.from_microseconds(test_micros)
print(f"\nTest datetime from arbitrary microseconds: {test_dt}")
print(f"Has timezone? {test_dt.tzinfo}")
print(f"Timezone value: {test_dt.tzinfo}")

# Actually the bug is in my test! Let me re-read the implementation
# from_microseconds returns: _UTC_EPOCH + datetime.timedelta(microseconds=value)
# where _UTC_EPOCH = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

# So it SHOULD have timezone info. Let me double-check
import datetime as dt_module
_UTC_EPOCH = dt_module.datetime(1970, 1, 1, tzinfo=dt_module.timezone.utc)
result = _UTC_EPOCH + dt_module.timedelta(microseconds=1000000)
print(f"\nDirect calculation: {result}")
print(f"Has timezone? {result.tzinfo}")

# Ah! The issue is that adding timedelta to a timezone-aware datetime 
# preserves the timezone. So from_microseconds DOES return a timezone-aware datetime.
# But my test assertion is wrong!