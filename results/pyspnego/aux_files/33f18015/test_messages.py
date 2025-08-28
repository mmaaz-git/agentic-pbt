#!/usr/bin/env /root/hypothesis-llm/envs/pyspnego_env/bin/python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

import spnego._ntlm_raw.messages as messages

print("Testing NTLM message serialization properties...")
print("=" * 60)

# Test Version round-trip
print("\nTest: Version round-trip")
version = messages.Version(10, 0, 19041, 1)
print(f"  Original: major={version.major}, minor={version.minor}, build={version.build}, revision={version.revision}")
packed = version.pack()
print(f"  Packed bytes: {packed.hex()} (length={len(packed)})")
unpacked = messages.Version.unpack(packed)
print(f"  Unpacked: major={unpacked.major}, minor={unpacked.minor}, build={unpacked.build}, revision={unpacked.revision}")
success = (version.major == unpacked.major and version.minor == unpacked.minor and 
          version.build == unpacked.build and version.revision == unpacked.revision)
print(f"  Round-trip success: {success}")

# Test FileTime round-trip
print("\nTest: FileTime round-trip")
import time
# Current time in Windows FileTime format (100-nanosecond intervals since 1601)
current_time = int((time.time() + 11644473600) * 10000000)
ft = messages.FileTime(current_time)
print(f"  Original filetime: {ft.filetime}")
packed = ft.pack()
print(f"  Packed bytes: {packed.hex()} (length={len(packed)})")
unpacked = messages.FileTime.unpack(packed)
print(f"  Unpacked filetime: {unpacked.filetime}")
print(f"  Round-trip success: {ft.filetime == unpacked.filetime}")

# Test Negotiate message round-trip
print("\nTest: Negotiate message round-trip")
flags = messages.NegotiateFlags.unicode | messages.NegotiateFlags.oem | messages.NegotiateFlags.request_target
negotiate = messages.Negotiate(flags)
print(f"  Original flags: {hex(negotiate.flags)}")
packed = negotiate.pack()
print(f"  Packed length: {len(packed)} bytes")
print(f"  First 16 bytes: {packed[:16].hex()}")
unpacked = messages.Negotiate.unpack(packed)
print(f"  Unpacked flags: {hex(unpacked.flags)}")
print(f"  Round-trip success: {negotiate.flags == unpacked.flags}")

# Test with version included
print("\nTest: Negotiate with Version")
negotiate_with_ver = messages.Negotiate(
    messages.NegotiateFlags.unicode | messages.NegotiateFlags.version,
    version=messages.Version(10, 0, 19041, 1)
)
packed = negotiate_with_ver.pack()
print(f"  Packed length: {len(packed)} bytes")
unpacked = messages.Negotiate.unpack(packed)
print(f"  Flags preserved: {negotiate_with_ver.flags == unpacked.flags}")
if unpacked.version:
    print(f"  Version preserved: major={unpacked.version.major}, minor={unpacked.version.minor}")
    
# Test empty TargetInfo
print("\nTest: TargetInfo round-trip")
target_info = messages.TargetInfo()
packed = target_info.pack()
print(f"  Empty TargetInfo packed: {packed.hex()}")
unpacked = messages.TargetInfo.unpack(packed)
print(f"  Round-trip of empty TargetInfo: {len(unpacked.av_pairs) == 0}")

# Test TargetInfo with data
target_info_with_data = messages.TargetInfo([
    messages.AvPair(messages.AvId.dns_domain_name, "EXAMPLE.COM"),
    messages.AvPair(messages.AvId.dns_computer_name, "SERVER01")
])
packed = target_info_with_data.pack()
print(f"  TargetInfo with data packed length: {len(packed)} bytes")
unpacked = messages.TargetInfo.unpack(packed)
print(f"  Number of AV pairs unpacked: {len(unpacked.av_pairs)}")
if len(unpacked.av_pairs) >= 2:
    print(f"  First pair: {unpacked.av_pairs[0].id} = {unpacked.av_pairs[0].value}")
    print(f"  Second pair: {unpacked.av_pairs[1].id} = {unpacked.av_pairs[1].value}")