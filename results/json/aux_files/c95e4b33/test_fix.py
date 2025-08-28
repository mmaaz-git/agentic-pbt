from urllib.parse import urlparse

def should_strip_auth_fixed(old_url, new_url):
    """Fixed version that handles invalid ports gracefully"""
    try:
        old_parsed = urlparse(old_url)
        new_parsed = urlparse(new_url)
        
        # Try to access ports - may raise ValueError for invalid ports
        try:
            old_port = old_parsed.port
        except ValueError:
            # Invalid port in old URL - treat as different (strip auth for safety)
            return True
            
        try:
            new_port = new_parsed.port
        except ValueError:
            # Invalid port in new URL - treat as different (strip auth for safety)
            return True
        
        # Rest of the logic (simplified for demo)
        if old_parsed.hostname != new_parsed.hostname:
            return True
            
        # Special case: allow http -> https redirect on standard ports
        if (old_parsed.scheme == "http" and old_port in (80, None) and
            new_parsed.scheme == "https" and new_port in (443, None)):
            return False
            
        # Check if port or scheme changed
        changed_port = old_port != new_port
        changed_scheme = old_parsed.scheme != new_parsed.scheme
        
        return changed_port or changed_scheme
        
    except Exception:
        # Any other parsing error - strip auth for safety
        return True


# Test the fix
test_cases = [
    ("http://example.com/", "http://example.com:99999/"),  # Invalid port
    ("http://example.com:99999/", "http://example.com/"),  # Invalid port in old
    ("http://example.com:80/", "https://example.com:443/"),  # Special case
    ("http://example.com/", "http://other.com/"),  # Different host
]

for old, new in test_cases:
    try:
        result = should_strip_auth_fixed(old, new)
        print(f"Fixed: {old} -> {new}: strip_auth={result}")
    except Exception as e:
        print(f"Still crashes: {e}")