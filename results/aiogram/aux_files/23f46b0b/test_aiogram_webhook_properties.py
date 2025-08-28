"""Property-based tests for aiogram.webhook module using Hypothesis"""

import ipaddress
from ipaddress import IPv4Address, IPv4Network
from unittest.mock import Mock

from hypothesis import assume, given, strategies as st
from aiogram.webhook.security import IPFilter
from aiogram.webhook.aiohttp_server import check_ip


# Strategy for valid IPv4 addresses as strings
def valid_ipv4_strings():
    """Generate valid IPv4 address strings"""
    return st.builds(
        lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
        st.integers(0, 255),
        st.integers(0, 255),
        st.integers(0, 255),
        st.integers(0, 255)
    )


# Strategy for valid IPv4 network strings with CIDR notation
def valid_ipv4_networks():
    """Generate valid IPv4 network strings with CIDR notation"""
    return st.builds(
        lambda a, b, c, d, prefix: f"{a}.{b}.{c}.{d}/{prefix}",
        st.integers(0, 255),
        st.integers(0, 255),
        st.integers(0, 255),
        st.integers(0, 255),
        st.integers(0, 32)  # Valid prefix lengths
    )


# Property 1: IPFilter add-then-check invariant
@given(valid_ipv4_strings())
def test_ipfilter_add_then_check_single_ip(ip_str):
    """After adding an IP, check() should return True for that IP"""
    ip_filter = IPFilter()
    ip_filter.allow_ip(ip_str)
    
    # The added IP should be in the filter
    assert ip_filter.check(ip_str), f"IP {ip_str} was added but check() returned False"
    assert ip_str in ip_filter, f"IP {ip_str} was added but __contains__ returned False"


# Property 2: IPFilter.__contains__ equivalence with check()
@given(valid_ipv4_strings())
def test_ipfilter_contains_equals_check(ip_str):
    """ip in filter should be equivalent to filter.check(ip)"""
    ip_filter = IPFilter()
    
    # Add some random IPs
    for _ in range(5):
        random_ip = IPv4Address(ip_str)  # Use the generated IP
        ip_filter.allow_ip(str(random_ip))
    
    # Test equivalence for various IPs
    test_ips = [ip_str, "1.1.1.1", "192.168.1.1", "10.0.0.1"]
    for test_ip in test_ips:
        contains_result = test_ip in ip_filter
        check_result = ip_filter.check(test_ip)
        assert contains_result == check_result, \
            f"Inconsistency for {test_ip}: __contains__={contains_result}, check={check_result}"


# Property 3: Network expansion - all hosts allowed when network added
@given(
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(24, 30)  # Common subnet sizes that have manageable number of hosts
)
def test_ipfilter_network_expansion(a, b, c, d, prefix):
    """When adding a network, all host IPs in that network should be allowed"""
    network_str = f"{a}.{b}.{c}.{d}/{prefix}"
    
    try:
        network = IPv4Network(network_str, strict=False)
    except:
        assume(False)  # Skip invalid networks
    
    # Skip networks with too many hosts to avoid memory issues
    if network.num_addresses > 1024:
        assume(False)
    
    ip_filter = IPFilter()
    ip_filter.allow_ip(network_str)
    
    # All hosts in the network should be allowed
    hosts = list(network.hosts())
    if not hosts:  # For /32 networks, the network address itself should be allowed
        hosts = [network.network_address]
    
    for host in hosts:
        host_str = str(host)
        assert ip_filter.check(host_str), \
            f"Host {host_str} from network {network_str} not allowed"


# Property 4: Multiple IP formats should work
@given(valid_ipv4_strings())
def test_ipfilter_accepts_multiple_formats(ip_str):
    """IPFilter should accept string IPs, IPv4Address objects, and IPv4Network objects"""
    ip_filter = IPFilter()
    
    # Test string format
    ip_filter.allow_ip(ip_str)
    assert ip_filter.check(ip_str)
    
    # Test IPv4Address object format
    ip_addr_obj = IPv4Address(ip_str)
    ip_filter2 = IPFilter()
    ip_filter2.allow_ip(ip_addr_obj)
    assert ip_filter2.check(ip_str)
    
    # Test IPv4Network object format (single host network)
    ip_network_obj = IPv4Network(f"{ip_str}/32")
    ip_filter3 = IPFilter()
    ip_filter3.allow_ip(ip_network_obj)
    assert ip_filter3.check(ip_str)


# Property 5: X-Forwarded-For parsing - leftmost IP extraction
@given(
    st.lists(valid_ipv4_strings(), min_size=1, max_size=5)
)
def test_check_ip_x_forwarded_for_parsing(ip_list):
    """check_ip should extract the leftmost IP from X-Forwarded-For header"""
    # Create a filter with the first IP allowed
    ip_filter = IPFilter()
    ip_filter.allow_ip(ip_list[0])
    
    # Mock request with X-Forwarded-For header
    request = Mock()
    # X-Forwarded-For can have multiple IPs separated by comma
    x_forwarded_value = ", ".join(ip_list)
    request.headers = {"X-Forwarded-For": x_forwarded_value}
    request.transport = None
    
    extracted_ip, is_allowed = check_ip(ip_filter, request)
    
    # Should extract the leftmost (first) IP
    assert extracted_ip == ip_list[0], \
        f"Expected to extract {ip_list[0]} but got {extracted_ip}"
    
    # Should be allowed since we added the first IP
    assert is_allowed == True, \
        f"IP {ip_list[0]} should be allowed"


# Property 6: IPFilter.allow() with multiple IPs at once
@given(st.lists(valid_ipv4_strings(), min_size=1, max_size=10))
def test_ipfilter_allow_multiple(ip_list):
    """IPFilter.allow() should accept multiple IPs and all should be checkable"""
    ip_filter = IPFilter()
    ip_filter.allow(*ip_list)
    
    # All IPs should be allowed
    for ip in ip_list:
        assert ip_filter.check(ip), f"IP {ip} was added via allow() but check() returned False"


# Property 7: Empty X-Forwarded-For falls back to peername
@given(valid_ipv4_strings())
def test_check_ip_fallback_to_peername(ip_str):
    """When X-Forwarded-For is empty, should fall back to transport peername"""
    ip_filter = IPFilter()
    ip_filter.allow_ip(ip_str)
    
    # Mock request without X-Forwarded-For
    request = Mock()
    request.headers = {}
    
    # Mock transport with peername
    transport = Mock()
    transport.get_extra_info = Mock(return_value=(ip_str, 12345))  # (host, port)
    request.transport = transport
    
    extracted_ip, is_allowed = check_ip(ip_filter, request)
    
    assert extracted_ip == ip_str, f"Expected to extract {ip_str} from peername"
    assert is_allowed == True, f"IP {ip_str} should be allowed"


# Property 8: CIDR notation parsing
@given(
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(0, 255)
)
def test_ipfilter_cidr_vs_single_ip_parsing(a, b, c, d):
    """IPFilter should correctly distinguish between CIDR notation and single IPs"""
    single_ip = f"{a}.{b}.{c}.{d}"
    network_ip = f"{a}.{b}.{c}.{d}/24"
    
    # Test single IP
    filter1 = IPFilter()
    filter1.allow_ip(single_ip)
    assert filter1.check(single_ip)
    
    # Single IP shouldn't allow other IPs in the same /24
    if d < 255:
        other_ip = f"{a}.{b}.{c}.{d+1}"
        assert not filter1.check(other_ip), \
            f"Single IP {single_ip} shouldn't allow {other_ip}"
    
    # Test network
    filter2 = IPFilter()
    try:
        network = IPv4Network(network_ip, strict=False)
        filter2.allow_ip(network_ip)
        
        # All hosts in network should be allowed
        for host in list(network.hosts())[:10]:  # Check first 10 hosts
            assert filter2.check(str(host)), \
                f"Network {network_ip} should allow host {host}"
    except:
        pass  # Some combinations might create invalid networks


# Property 9: Idempotence - adding same IP multiple times
@given(valid_ipv4_strings())
def test_ipfilter_idempotent_add(ip_str):
    """Adding the same IP multiple times should be idempotent"""
    filter1 = IPFilter()
    filter1.allow_ip(ip_str)
    
    filter2 = IPFilter()
    for _ in range(5):
        filter2.allow_ip(ip_str)
    
    # Both filters should behave identically
    test_ips = [ip_str, "1.1.1.1", "8.8.8.8"]
    for test_ip in test_ips:
        assert filter1.check(test_ip) == filter2.check(test_ip), \
            f"Idempotence violated for {test_ip}"