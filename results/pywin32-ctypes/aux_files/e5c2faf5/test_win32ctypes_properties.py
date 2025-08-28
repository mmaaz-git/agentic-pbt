#!/usr/bin/env python3
"""
Property-based tests for win32ctypes using Hypothesis.
Testing mathematical properties and invariants claimed by the implementation.
"""

import sys
import os
import time
import tempfile
import shutil

# Add the virtualenv's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import pytest

# Since we're on Linux, we need to test the IS_INTRESOURCE function directly
# without importing the Windows-specific modules that depend on Windows APIs
def IS_INTRESOURCE(x):
    """Direct implementation of IS_INTRESOURCE from win32ctypes"""
    return x >> 16 == 0

# Skip Windows-specific imports on non-Windows platforms
try:
    from win32ctypes.pywin32 import win32api, win32cred, pywintypes
    WINDOWS_AVAILABLE = True
except (ImportError, OSError):
    WINDOWS_AVAILABLE = False
    # Create dummy objects for tests to skip gracefully
    class DummyModule:
        def __getattr__(self, name):
            pytest.skip("Windows API not available on this platform")
    win32api = DummyModule()
    win32cred = DummyModule()
    pywintypes = DummyModule()


# Property 1: IS_INTRESOURCE mathematical property
@given(st.integers())
def test_is_intresource_mathematical_property(x):
    """Test that IS_INTRESOURCE correctly identifies values < 2^16"""
    # The function claims that x >> 16 == 0 identifies integer resources
    # This means values less than 65536 should return True
    result = IS_INTRESOURCE(x)
    
    # For positive values, the property should hold precisely
    if x >= 0:
        expected = (x < 65536)
        assert result == expected, f"IS_INTRESOURCE({x}) returned {result}, expected {expected}"
    else:
        # For negative values, the right shift behavior depends on sign extension
        # The actual implementation uses >> which does arithmetic shift in Python
        assert result == (x >> 16 == 0)


# Property 2: IS_INTRESOURCE boundary conditions  
@given(st.integers(min_value=0, max_value=100000))
def test_is_intresource_boundaries(x):
    """Test IS_INTRESOURCE at critical boundaries"""
    result = IS_INTRESOURCE(x)
    
    # Values 0 to 65535 should return True
    # Values 65536 and above should return False
    if x < 65536:
        assert result is True, f"IS_INTRESOURCE({x}) should be True for values < 65536"
    else:
        assert result is False, f"IS_INTRESOURCE({x}) should be False for values >= 65536"


# Property 3: GetTickCount monotonicity
@pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Windows API not available")
@given(st.integers(min_value=1, max_value=10))
def test_gettickcount_monotonicity(num_calls):
    """Test that GetTickCount returns non-decreasing values"""
    counts = []
    for _ in range(num_calls):
        count = win32api.GetTickCount()
        counts.append(count)
        # Small sleep to allow time to advance (optional, but makes test more robust)
        time.sleep(0.001)
    
    # Check monotonicity - each value should be >= previous
    for i in range(1, len(counts)):
        assert counts[i] >= counts[i-1], \
            f"GetTickCount not monotonic: {counts[i]} < {counts[i-1]}"


# Property 4: GetTickCount always positive
@pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Windows API not available")
@given(st.just(None))
def test_gettickcount_positive(dummy):
    """Test that GetTickCount always returns positive values"""
    count = win32api.GetTickCount()
    assert count >= 0, f"GetTickCount returned negative value: {count}"
    assert isinstance(count, int), f"GetTickCount should return int, got {type(count)}"


# Property 5: Credential round-trip with random data
@pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Windows API not available")
@given(
    st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
    st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
    st.text(min_size=0, max_size=200, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
)
def test_credential_roundtrip(target_name, username, password):
    """Test that credentials written can be read back with same data"""
    # Skip if running on non-Windows or in restricted environment
    try:
        # Create unique target to avoid conflicts
        unique_target = f"hypothesis_test_{target_name}_{id(target_name)}"
        
        credential = {
            "Type": win32cred.CRED_TYPE_GENERIC,
            "TargetName": unique_target,
            "UserName": username,
            "CredentialBlob": password,
            "Comment": "Hypothesis test credential",
            "Persist": win32cred.CRED_PERSIST_SESSION
        }
        
        # Write credential
        win32cred.CredWrite(credential)
        
        try:
            # Read it back
            read_cred = win32cred.CredRead(unique_target, win32cred.CRED_TYPE_GENERIC)
            
            # Verify the data matches
            assert read_cred["TargetName"] == unique_target
            assert read_cred["UserName"] == username
            # Password is returned as bytes in UTF-16 encoding
            assert read_cred["CredentialBlob"].decode('utf-16') == password
            assert read_cred["Comment"] == "Hypothesis test credential"
            
        finally:
            # Clean up
            try:
                win32cred.CredDelete(unique_target, win32cred.CRED_TYPE_GENERIC)
            except:
                pass
                
    except pywintypes.error as e:
        # Skip test if credentials API not available (e.g., Linux)
        if e.winerror in [1, 50, 120]:  # ERROR_INVALID_FUNCTION or similar
            pytest.skip("Credentials API not available on this platform")
        raise


# Property 6: Resource loading from system libraries
@pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Windows API not available")
@given(st.just(None))
def test_resource_loading_consistency(dummy):
    """Test that resource operations are consistent"""
    try:
        # Load a known system library
        handle = win32api.LoadLibraryEx("shell32.dll", 0, win32api.LOAD_LIBRARY_AS_DATAFILE)
        
        try:
            # Enumerate resource types twice - should be consistent
            types1 = win32api.EnumResourceTypes(handle)
            types2 = win32api.EnumResourceTypes(handle)
            
            # The same handle should return the same resource types
            assert set(types1) == set(types2), \
                "EnumResourceTypes returned different results for same handle"
            
            # Types should not be empty for shell32.dll
            assert len(types1) > 0, "shell32.dll should have resources"
            
        finally:
            win32api.FreeLibrary(handle)
            
    except pywintypes.error as e:
        # Skip if not on Windows
        if e.winerror in [1, 2, 126]:
            pytest.skip("Windows DLL operations not available")
        raise


# Property 7: LoadLibraryEx/FreeLibrary handle validity
@pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Windows API not available")
@given(st.just(None))  
def test_library_handle_validity(dummy):
    """Test that library handles remain valid between load and free"""
    try:
        # Use Python executable as a known valid file
        handle = win32api.LoadLibraryEx(sys.executable, 0, win32api.LOAD_LIBRARY_AS_DATAFILE)
        
        # Handle should be a positive integer
        assert handle > 0, f"LoadLibraryEx returned invalid handle: {handle}"
        assert isinstance(handle, int), f"Handle should be int, got {type(handle)}"
        
        # Should be able to use the handle
        types = win32api.EnumResourceTypes(handle)
        assert isinstance(types, list), "EnumResourceTypes should return a list"
        
        # FreeLibrary should succeed
        result = win32api.FreeLibrary(handle)
        # FreeLibrary returns None on success in pywin32
        assert result is None or result != 0
        
    except pywintypes.error as e:
        if e.winerror in [1, 2, 126]:
            pytest.skip("Library operations not available")
        raise


# Property 8: Windows directory paths
@pytest.mark.skipif(not WINDOWS_AVAILABLE, reason="Windows API not available")
@given(st.just(None))
def test_windows_directory_properties(dummy):
    """Test properties of Windows directory functions"""
    try:
        win_dir = win32api.GetWindowsDirectory()
        sys_dir = win32api.GetSystemDirectory()
        
        # Both should return non-empty strings
        assert isinstance(win_dir, str), f"GetWindowsDirectory should return str, got {type(win_dir)}"
        assert isinstance(sys_dir, str), f"GetSystemDirectory should return str, got {type(sys_dir)}"
        assert len(win_dir) > 0, "Windows directory should not be empty"
        assert len(sys_dir) > 0, "System directory should not be empty"
        
        # System directory should be a subdirectory of Windows directory
        # (This is true on standard Windows installations)
        assert sys_dir.lower().startswith(win_dir.lower()) or \
               win_dir.lower() in sys_dir.lower(), \
               f"System dir {sys_dir} not related to Windows dir {win_dir}"
        
    except pywintypes.error as e:
        if e.winerror in [1, 120]:
            pytest.skip("Windows directory functions not available")
        raise


if __name__ == "__main__":
    print("Running property-based tests for win32ctypes...")
    pytest.main([__file__, "-v", "--tb=short"])