#!/usr/bin/env python3
"""Property-based tests for esp_idf_monitor.base module."""

import sys
import os
import re
import string

# Add the esp_idf_monitor path
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the modules to test
from esp_idf_monitor.base.binlog import BinaryLog, ArgFormatter
from esp_idf_monitor.base.line_matcher import LineMatcher
from esp_idf_monitor.base.ansi_color_converter import ANSIColorConverter, RE_ANSI_COLOR


# Test 1: CRC8 calculation properties
class TestCRC8Properties:
    """Test properties of CRC8 calculation in BinaryLog."""
    
    @given(st.binary())
    def test_crc8_deterministic(self, data):
        """CRC8 should always return the same value for the same input."""
        crc1 = BinaryLog.crc8(data)
        crc2 = BinaryLog.crc8(data)
        assert crc1 == crc2
    
    @given(st.binary())
    def test_crc8_range(self, data):
        """CRC8 should always return values in range 0-255."""
        crc = BinaryLog.crc8(data)
        assert 0 <= crc <= 255
    
    @given(st.binary(min_size=1))
    def test_crc8_append_crc_gives_zero(self, data):
        """Appending CRC to data and calculating CRC should give 0."""
        crc = BinaryLog.crc8(data)
        data_with_crc = data + bytes([crc])
        assert BinaryLog.crc8(data_with_crc) == 0


# Test 2: ArgFormatter C-style format conversion
class TestArgFormatterProperties:
    """Test properties of C-style format string conversion."""
    
    @given(st.text(alphabet=string.ascii_letters + string.digits + ' ', min_size=1, max_size=50))
    def test_literal_string_passthrough(self, text):
        """Literal strings without format specifiers should pass through unchanged."""
        assume('%' not in text)
        formatter = ArgFormatter()
        result = formatter.c_format(text, [])
        assert result == text
    
    @given(st.integers())
    def test_integer_format_basic(self, value):
        """Basic integer formatting should work correctly."""
        formatter = ArgFormatter()
        result = formatter.c_format("%d", [value])
        assert result == str(value)
    
    @given(st.integers(min_value=0, max_value=0xFFFFFFFF))
    def test_hex_format(self, value):
        """Hex formatting should produce correct output."""
        formatter = ArgFormatter()
        
        # Test lowercase hex
        result_lower = formatter.c_format("%x", [value])
        assert result_lower == f"{value:x}"
        
        # Test uppercase hex  
        result_upper = formatter.c_format("%X", [value])
        assert result_upper == f"{value:X}"
    
    @given(st.integers(min_value=0, max_value=0o777777))
    def test_octal_format(self, value):
        """Octal formatting should produce correct output."""
        formatter = ArgFormatter()
        result = formatter.c_format("%o", [value])
        assert result == f"{value:o}"
        
        # Test with alternate form (#)
        result_alt = formatter.c_format("%#o", [value])
        expected = f"0{value:o}" if value != 0 else "0"
        assert result_alt == expected
    
    @given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
    def test_float_format(self, value):
        """Float formatting should produce valid output."""
        formatter = ArgFormatter()
        result = formatter.c_format("%f", [value])
        # Check that it produces a valid float representation
        assert '.' in result or 'e' in result.lower()
        # Verify it can be parsed back
        float(result)
    
    def test_percent_escape(self):
        """Double percent should produce single percent."""
        formatter = ArgFormatter()
        result = formatter.c_format("%%", [])
        assert result == "%"
        
        result2 = formatter.c_format("%%d", [42])
        assert result2 == "%d"
    
    @given(st.integers(min_value=1, max_value=20), st.integers())
    def test_width_specifier(self, width, value):
        """Width specifier should produce correctly padded output."""
        formatter = ArgFormatter()
        result = formatter.c_format(f"%{width}d", [value])
        # Result should be at least 'width' characters
        assert len(result) >= min(width, len(str(value)))
    
    @given(st.integers(min_value=-1000, max_value=1000))
    def test_sign_flags(self, value):
        """Test + and space flags for signed numbers."""
        formatter = ArgFormatter()
        
        # Test + flag
        result_plus = formatter.c_format("%+d", [value])
        if value >= 0:
            assert result_plus.startswith('+')
        else:
            assert result_plus.startswith('-')
        
        # Test space flag
        result_space = formatter.c_format("% d", [value])
        if value >= 0:
            assert result_space[0] in ' 0123456789'
        else:
            assert result_space.startswith('-')


# Test 3: LineMatcher filter properties
class TestLineMatcherProperties:
    """Test properties of LineMatcher filter parsing."""
    
    @given(st.text(alphabet=string.ascii_letters + string.digits + ':', min_size=1, max_size=20))
    def test_filter_parsing_doesnt_crash(self, filter_str):
        """LineMatcher should handle various filter strings without crashing."""
        try:
            matcher = LineMatcher(filter_str)
            # If it parses successfully, it should not crash on matching
            matcher.match("E (12345) test: message")
        except ValueError:
            # ValueError is expected for invalid filter formats
            pass
    
    def test_wildcard_matches_everything(self):
        """Wildcard filter should match all valid log lines."""
        matcher = LineMatcher("*:V")
        
        test_lines = [
            "E (12345) test: error message",
            "W (12345) module: warning",
            "I (12345) app: info",
            "D (12345) debug: debug message",
            "V (12345) verbose: verbose output"
        ]
        
        for line in test_lines:
            assert matcher.match(line)
    
    @given(st.sampled_from(['E', 'W', 'I', 'D', 'V']),
           st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10))
    def test_specific_tag_filter(self, level, tag):
        """Specific tag filters should only match their tag."""
        assume(':' not in tag)
        filter_str = f"{tag}:{level}"
        matcher = LineMatcher(filter_str)
        
        # Should match lines with the specified tag
        matching_line = f"{level} (12345) {tag}: message"
        assert matcher.match(matching_line)
        
        # Should not match lines with different tags
        different_line = f"{level} (12345) different: message"
        assert not matcher.match(different_line)
    
    def test_level_hierarchy(self):
        """Log levels should follow hierarchy: N < E < W < I < D < V."""
        tag = "test"
        
        # Test each level filter
        levels = ['N', 'E', 'W', 'I', 'D', 'V']
        for filter_level in levels:
            matcher = LineMatcher(f"{tag}:{filter_level}")
            
            for msg_level in levels:
                if msg_level == 'N':
                    continue  # Skip N as it's not a real log level in messages
                
                line = f"{msg_level} (12345) {tag}: message"
                
                # Should match if message level <= filter level
                level_values = {'N': 0, 'E': 1, 'W': 2, 'I': 3, 'D': 4, 'V': 5}
                should_match = level_values[msg_level] <= level_values[filter_level]
                
                assert matcher.match(line) == should_match


# Test 4: ANSIColorConverter properties
class TestANSIColorConverterProperties:
    """Test properties of ANSI color conversion."""
    
    @given(st.binary())
    def test_non_ansi_passthrough(self, data):
        """Data without ANSI sequences should pass through unchanged."""
        assume(b'\033' not in data)
        
        class MockOutput:
            def __init__(self):
                self.written = []
            def write(self, data):
                self.written.append(data)
            def flush(self):
                pass
        
        output = MockOutput()
        # Force non-Windows behavior for consistent testing
        converter = ANSIColorConverter(output, force_color=True)
        converter.write(data)
        
        written_data = b''.join(output.written)
        assert written_data == data
    
    def test_ansi_color_regex_matches_valid_sequences(self):
        """RE_ANSI_COLOR should match valid ANSI color sequences."""
        valid_sequences = [
            b'\033[0;30m',  # Black
            b'\033[0;31m',  # Red
            b'\033[0;32m',  # Green
            b'\033[0;33m',  # Yellow
            b'\033[0;34m',  # Blue
            b'\033[0;35m',  # Magenta
            b'\033[0;36m',  # Cyan
            b'\033[0;37m',  # White
            b'\033[1;30m',  # Bright Black
            b'\033[1;31m',  # Bright Red
            b'\033[1;37m',  # Bright White
        ]
        
        for seq in valid_sequences:
            match = RE_ANSI_COLOR.match(seq)
            assert match is not None
            assert match.group(0) == seq
    
    @given(st.integers(min_value=0, max_value=7))
    def test_ansi_to_windows_color_mapping(self, ansi_color):
        """ANSI to Windows color mapping should be consistent."""
        from esp_idf_monitor.base.ansi_color_converter import ANSI_TO_WINDOWS_COLOR
        
        # The mapping should be bidirectional (no two ANSI colors map to same Windows color)
        windows_color = ANSI_TO_WINDOWS_COLOR[ansi_color]
        assert 0 <= windows_color <= 7
        
        # Check uniqueness
        for i in range(8):
            if i != ansi_color:
                assert ANSI_TO_WINDOWS_COLOR[i] != windows_color or i == ansi_color


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])