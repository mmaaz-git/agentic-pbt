#!/usr/bin/env python3
"""
Minimal reproductions of bugs in troposphere.servicediscovery
"""

from troposphere.servicediscovery import DnsRecord, SOA

print("Bug 1: Invalid JSON with infinity values")
print("-" * 40)
dns_record = DnsRecord(TTL=float('inf'), Type='A')
json_output = dns_record.to_json()
print(f"Generated JSON:\n{json_output}")
print("Issue: 'Infinity' is not valid JSON per RFC 7159")
print("CloudFormation will reject this template")
print()

print("Bug 2: Invalid JSON with NaN values")
print("-" * 40)
dns_record = DnsRecord(TTL=float('nan'), Type='A')
json_output = dns_record.to_json()
print(f"Generated JSON:\n{json_output}")
print("Issue: 'NaN' is not valid JSON per RFC 7159")
print("CloudFormation will reject this template")
print()

print("Bug 3: Negative TTL values accepted")
print("-" * 40)
dns_record = DnsRecord(TTL=-100, Type='A')
print(f"Created DnsRecord with TTL=-100: {dns_record.to_dict()}")
print("Issue: DNS TTL values must be non-negative (0-2147483647)")
print("CloudFormation will reject negative TTL")
print()

print("Bug 4: Boolean values accepted as TTL")
print("-" * 40)
dns_record = DnsRecord(TTL=True, Type='A')
print(f"Created DnsRecord with TTL=True: {dns_record.to_dict()}")
dns_record2 = DnsRecord(TTL=False, Type='CNAME')
print(f"Created DnsRecord with TTL=False: {dns_record2.to_dict()}")
print("Issue: TTL should be numeric, not boolean")
print()

print("Bug 5: TTL values beyond CloudFormation limits")
print("-" * 40)
huge_ttl = 2**32  # 4294967296
dns_record = DnsRecord(TTL=huge_ttl, Type='A')
print(f"Created DnsRecord with TTL={huge_ttl}: {dns_record.to_dict()}")
print("Issue: CloudFormation TTL limit is 2147483647 (2^31-1)")
print("Values beyond this will be rejected by CloudFormation")