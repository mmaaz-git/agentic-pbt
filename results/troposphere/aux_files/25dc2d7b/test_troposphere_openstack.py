#!/usr/bin/env python3
"""Property-based tests for troposphere.openstack module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import pytest

# Import the modules we're testing
from troposphere.openstack import neutron, nova, heat


# Test for Server.validate() bug - line 143 uses wrong key
@given(
    image_update_policy=st.sampled_from(["REBUILD", "REPLACE", "REBUILD_PRESERVE_EPHEMERAL", "INVALID"])
)
def test_server_image_update_policy_validation_bug(image_update_policy):
    """Test that Server.validate() checks image_update_policy correctly.
    
    Bug: Line 143 in nova.py incorrectly uses self.resource["flavor_update_policy"]
    when checking image_update_policy validation.
    """
    server = nova.Server("testserver", image="testimage", networks=[])
    server.resource["image_update_policy"] = image_update_policy
    
    if image_update_policy not in ["REBUILD", "REPLACE", "REBUILD_PRESERVE_EPHEMERAL"]:
        with pytest.raises(ValueError) as exc_info:
            server.validate()
        assert "image_update_policy" in str(exc_info.value)
    else:
        server.validate()  # Should not raise


# Test SessionPersistence validation logic bug
@given(
    session_type=st.sampled_from(["SOURCE_IP", "HTTP_COOKIE", "APP_COOKIE", None]),
    has_cookie_name=st.booleans()
)
def test_session_persistence_validation_logic(session_type, has_cookie_name):
    """Test SessionPersistence validation logic.
    
    Bug: The validation checks for cookie_name without first verifying 
    that type is APP_COOKIE.
    """
    props = {}
    if session_type is not None:
        props["type"] = session_type
    if has_cookie_name:
        props["cookie_name"] = "test_cookie"
    
    session = neutron.SessionPersistence(**props)
    
    # The validation logic is flawed - it checks for cookie_name before checking type value
    if "type" in props:
        if "cookie_name" not in props:
            # Bug: This should only be required when type is APP_COOKIE
            with pytest.raises(ValueError) as exc_info:
                session.validate()
            assert "cookie_name" in str(exc_info.value)
        elif props["type"] not in ["SOURCE_IP", "HTTP_COOKIE", "APP_COOKIE"]:
            with pytest.raises(ValueError):
                session.validate()
        else:
            session.validate()
    else:
        session.validate()  # Should not raise if no type


# Test FirewallRule validation
@given(
    action=st.one_of(st.none(), st.sampled_from(["allow", "deny", "invalid"])),
    ip_version=st.one_of(st.none(), st.sampled_from(["4", "6", "5"])),
    protocol=st.one_of(st.none(), st.sampled_from(["tcp", "udp", "icmp", None, "invalid"]))
)
def test_firewall_rule_validation(action, ip_version, protocol):
    """Test FirewallRule validation for enum fields."""
    rule = neutron.FirewallRule("testrule")
    
    if action is not None:
        rule.resource["action"] = action
    if ip_version is not None:
        rule.resource["ip_version"] = ip_version
    if protocol is not None:
        rule.resource["protocol"] = protocol
    
    should_fail = False
    expected_error = []
    
    if action is not None and action not in ["allow", "deny"]:
        should_fail = True
        expected_error.append("action")
    if ip_version is not None and ip_version not in ["4", "6"]:
        should_fail = True
        expected_error.append("ip_version")
    if protocol is not None and protocol not in ["tcp", "udp", "icmp", None]:
        should_fail = True
        expected_error.append("protocol")
    
    if should_fail:
        with pytest.raises(ValueError) as exc_info:
            rule.validate()
        # Check that at least one expected error is in the message
        assert any(err in str(exc_info.value) for err in expected_error)
    else:
        rule.validate()  # Should not raise


# Test HealthMonitor validation
@given(
    monitor_type=st.sampled_from(["PING", "TCP", "HTTP", "HTTPS", "INVALID", "ping", "http"])
)
def test_health_monitor_type_validation(monitor_type):
    """Test HealthMonitor type validation - must be uppercase."""
    monitor = neutron.HealthMonitor(
        "testmonitor",
        type=monitor_type,
        delay=5,
        max_retries=3,
        timeout=10
    )
    monitor.resource["type"] = monitor_type
    
    if monitor_type not in ["PING", "TCP", "HTTP", "HTTPS"]:
        with pytest.raises(ValueError) as exc_info:
            monitor.validate()
        assert "type" in str(exc_info.value)
    else:
        monitor.validate()


# Test Pool validation
@given(
    lb_method=st.sampled_from(["ROUND_ROBIN", "LEAST_CONNECTIONS", "SOURCE_IP", "RANDOM"]),
    protocol=st.sampled_from(["TCP", "HTTP", "HTTPS", "UDP"])
)
def test_pool_validation(lb_method, protocol):
    """Test Pool lb_method and protocol validation."""
    pool = neutron.Pool(
        "testpool",
        lb_method=lb_method,
        protocol=protocol,
        subnet_id="testsubnet"
    )
    pool.resource["lb_method"] = lb_method
    pool.resource["protocol"] = protocol
    
    should_fail = False
    if lb_method not in ["ROUND_ROBIN", "LEAST_CONNECTIONS", "SOURCE_IP"]:
        should_fail = True
    if protocol not in ["TCP", "HTTP", "HTTPS"]:
        should_fail = True
    
    if should_fail:
        with pytest.raises(ValueError):
            pool.validate()
    else:
        pool.validate()


# Test SecurityGroupRule validation
@given(
    direction=st.one_of(st.none(), st.sampled_from(["ingress", "egress", "both"])),
    ethertype=st.one_of(st.none(), st.sampled_from(["IPv4", "IPv6", "IPv5"])),
    protocol=st.one_of(st.none(), st.sampled_from(["tcp", "udp", "icmp", "all"])),
    remote_mode=st.one_of(st.none(), st.sampled_from(["remote_ip_prefix", "remote_group_id", "both"]))
)
def test_security_group_rule_validation(direction, ethertype, protocol, remote_mode):
    """Test SecurityGroupRule validation for all enum fields."""
    rule = neutron.SecurityGroupRule()
    
    if direction is not None:
        rule.resource["direction"] = direction
    if ethertype is not None:
        rule.resource["ethertype"] = ethertype
    if protocol is not None:
        rule.resource["protocol"] = protocol
    if remote_mode is not None:
        rule.resource["remote_mode"] = remote_mode
    
    should_fail = False
    if direction is not None and direction not in ["ingress", "egress"]:
        should_fail = True
    if ethertype is not None and ethertype not in ["IPv4", "IPv6"]:
        should_fail = True
    if protocol is not None and protocol not in ["tcp", "udp", "icmp"]:
        should_fail = True
    if remote_mode is not None and remote_mode not in ["remote_ip_prefix", "remote_group_id"]:
        should_fail = True
    
    if should_fail:
        with pytest.raises(ValueError):
            rule.validate()
    else:
        rule.validate()


# Test BlockDeviceMappingV2 validation
@given(
    device_type=st.one_of(st.none(), st.sampled_from(["cdrom", "disk", "floppy"])),
    disk_bus=st.one_of(st.none(), st.sampled_from(["ide", "lame_bus", "scsi", "usb", "virtio", "sata"])),
    ephemeral_format=st.one_of(st.none(), st.sampled_from(["ext2", "ext3", "ext4", "xfs", "ntfs", "fat32"]))
)
def test_block_device_mapping_v2_validation(device_type, disk_bus, ephemeral_format):
    """Test BlockDeviceMappingV2 validation for enum fields."""
    mapping = nova.BlockDeviceMappingV2()
    
    if device_type is not None:
        mapping.resource["device_type"] = device_type
    if disk_bus is not None:
        mapping.resource["disk_bus"] = disk_bus
    if ephemeral_format is not None:
        mapping.resource["ephemeral_format"] = ephemeral_format
    
    should_fail = False
    if device_type is not None and device_type not in ["cdrom", "disk"]:
        should_fail = True
    if disk_bus is not None and disk_bus not in ["ide", "lame_bus", "scsi", "usb", "virtio"]:
        should_fail = True
    if ephemeral_format is not None and ephemeral_format not in ["ext2", "ext3", "ext4", "xfs", "ntfs"]:
        should_fail = True
    
    if should_fail:
        with pytest.raises(ValueError):
            mapping.validate()
    else:
        mapping.validate()


# Test Server diskConfig validation
@given(
    disk_config=st.sampled_from(["AUTO", "MANUAL", "auto", "manual", "AUTOMATIC"])
)
def test_server_disk_config_validation(disk_config):
    """Test Server diskConfig validation - must be uppercase."""
    server = nova.Server("testserver", image="testimage", networks=[])
    server.resource["diskConfig"] = disk_config
    
    if disk_config not in ["AUTO", "MANUAL"]:
        with pytest.raises(ValueError) as exc_info:
            server.validate()
        assert "diskConfig" in str(exc_info.value)
    else:
        server.validate()


# Test Server flavor_update_policy validation
@given(
    policy=st.sampled_from(["RESIZE", "REPLACE", "RESTART", "resize", "replace"])
)
def test_server_flavor_update_policy_validation(policy):
    """Test Server flavor_update_policy validation."""
    server = nova.Server("testserver", image="testimage", networks=[])
    server.resource["flavor_update_policy"] = policy
    
    if policy not in ["RESIZE", "REPLACE"]:
        with pytest.raises(ValueError) as exc_info:
            server.validate()
        assert "flavor_update_policy" in str(exc_info.value)
    else:
        server.validate()


# Test Server software_config_transport validation
@given(
    transport=st.sampled_from(["POLL_SERVER_CFN", "POLL_SERVER_HEAT", "PUSH", "poll_server_cfn"])
)
def test_server_software_config_transport_validation(transport):
    """Test Server software_config_transport validation."""
    server = nova.Server("testserver", image="testimage", networks=[])
    server.resource["software_config_transport"] = transport
    
    if transport not in ["POLL_SERVER_CFN", "POLL_SERVER_HEAT"]:
        with pytest.raises(ValueError) as exc_info:
            server.validate()
        assert "software_config_transport" in str(exc_info.value)
    else:
        server.validate()


# Test Server user_data_format validation
@given(
    format_type=st.sampled_from(["HEAT_CFNTOOLS", "RAW", "JSON", "heat_cfntools", "raw"])
)
def test_server_user_data_format_validation(format_type):
    """Test Server user_data_format validation."""
    server = nova.Server("testserver", image="testimage", networks=[])
    server.resource["user_data_format"] = format_type
    
    if format_type not in ["HEAT_CFNTOOLS", "RAW"]:
        with pytest.raises(ValueError) as exc_info:
            server.validate()
        assert "user_data_format" in str(exc_info.value)
    else:
        server.validate()


# Test PoolMember weight range validation
@given(
    weight=st.integers(min_value=-10, max_value=300)
)
def test_pool_member_weight_range(weight):
    """Test PoolMember weight must be in range 0-256."""
    from troposphere.validators import integer_range
    
    # Test the validator directly since PoolMember uses integer_range(0, 256)
    validator = integer_range(0, 256)
    
    if 0 <= weight <= 256:
        # Should accept the value
        result = validator(weight)
        assert result == weight
    else:
        # Should raise ValueError for out of range
        with pytest.raises(ValueError) as exc_info:
            validator(weight)
        assert "0" in str(exc_info.value) and "256" in str(exc_info.value)


if __name__ == "__main__":
    # Run a quick smoke test
    print("Running property-based tests for troposphere.openstack...")
    print("\n=== Testing Server.image_update_policy bug ===")
    try:
        test_server_image_update_policy_validation_bug()
        print("PASSED (unexpected - bug may have been fixed)")
    except Exception as e:
        print(f"FAILED (as expected - found bug): {e}")
    
    print("\n=== Testing SessionPersistence validation ===")
    try:
        test_session_persistence_validation_logic()
        print("PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
    
    print("\nRun with pytest for full test suite.")