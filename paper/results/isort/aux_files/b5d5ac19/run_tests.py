#!/usr/bin/env python3
"""Run the property-based tests"""

import sys
import traceback

# Add test discovery
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, Verbosity
import isort.main
from isort.settings import Config
from isort.wrap_modes import WrapModes

print("Running property-based tests for isort.main...")
print("=" * 60)

# Test 1: Config wrap_length constraint
print("\n[Test 1] Testing Config wrap_length constraint...")
try:
    @given(
        line_length=st.integers(min_value=1, max_value=1000),
        wrap_length=st.integers(min_value=0, max_value=2000)
    )
    @settings(max_examples=100)
    def test_config_wrap_length_constraint(line_length, wrap_length):
        config_dict = {
            "line_length": line_length,
            "wrap_length": wrap_length
        }
        
        if wrap_length > line_length:
            try:
                Config(**config_dict)
                # Should have raised ValueError
                raise AssertionError(f"Expected ValueError for wrap_length={wrap_length} > line_length={line_length}")
            except ValueError as e:
                if "wrap_length must be set lower than or equal to line_length" not in str(e):
                    raise
        else:
            config = Config(**config_dict)
            assert config.wrap_length == wrap_length
            assert config.line_length == line_length
    
    test_config_wrap_length_constraint()
    print("✓ Config wrap_length constraint test passed")
except Exception as e:
    print(f"✗ Config wrap_length constraint test failed: {e}")
    traceback.print_exc()

# Test 2: parse_args handles mutually exclusive flags
print("\n[Test 2] Testing parse_args mutually exclusive flags...")
try:
    @given(
        include_float_to_top=st.booleans(),
        include_dont_float_to_top=st.booleans()
    )
    @settings(max_examples=10)
    def test_mutually_exclusive_flags(include_float_to_top, include_dont_float_to_top):
        args = []
        
        if include_float_to_top:
            args.append("--float-to-top")
        if include_dont_float_to_top:
            args.append("--dont-float-to-top")
        
        if include_float_to_top and include_dont_float_to_top:
            try:
                isort.main.parse_args(args)
                raise AssertionError("Expected SystemExit for mutually exclusive flags")
            except SystemExit:
                pass
        else:
            result = isort.main.parse_args(args)
            if include_dont_float_to_top:
                assert result.get("float_to_top") == False
            elif include_float_to_top:
                assert result.get("float_to_top") == True
    
    test_mutually_exclusive_flags()
    print("✓ Mutually exclusive flags test passed")
except Exception as e:
    print(f"✗ Mutually exclusive flags test failed: {e}")
    traceback.print_exc()

# Test 3: multi_line_output integer parsing
print("\n[Test 3] Testing multi_line_output integer parsing...")
try:
    @given(mode_int=st.integers(min_value=0, max_value=20))
    @settings(max_examples=30)
    def test_multi_line_output_int(mode_int):
        args = ["--multi-line", str(mode_int)]
        
        try:
            result = isort.main.parse_args(args)
            if "multi_line_output" in result:
                assert isinstance(result["multi_line_output"], WrapModes)
        except (ValueError, KeyError):
            # Invalid mode numbers should fail, which is expected
            pass
    
    test_multi_line_output_int()
    print("✓ Multi-line output integer parsing test passed")
except Exception as e:
    print(f"✗ Multi-line output integer parsing test failed: {e}")
    traceback.print_exc()

# Test 4: _preconvert function
print("\n[Test 4] Testing _preconvert function...")
try:
    @given(
        value=st.one_of(
            st.sets(st.text(max_size=5)),
            st.frozensets(st.integers()),
            st.text(),
            st.integers(),
            st.booleans(),
            st.lists(st.integers())
        )
    )
    @settings(max_examples=50)
    def test_preconvert(value):
        if isinstance(value, (set, frozenset)):
            result = isort.main._preconvert(value)
            assert isinstance(result, list)
            assert set(result) == set(value)
        else:
            # Test that it raises TypeError for unhandled types
            try:
                # Create a custom object that _preconvert won't handle
                class CustomObject:
                    pass
                
                isort.main._preconvert(CustomObject())
                raise AssertionError("Expected TypeError for unserializable object")
            except TypeError as e:
                assert "Unserializable object" in str(e)
    
    test_preconvert()
    print("✓ _preconvert function test passed")
except Exception as e:
    print(f"✗ _preconvert function test failed: {e}")
    traceback.print_exc()

# Test 5: Config py_version validation
print("\n[Test 5] Testing Config py_version validation...")
try:
    @given(py_version=st.text(min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_py_version_validation(py_version):
        if py_version == "auto" or py_version in ["2", "3", "27", "35", "36", "37", "38", "39", "310", "311", "312", "313", "all"]:
            # Should succeed for valid versions
            config = Config(py_version=py_version)
            if py_version != "all" and py_version != "auto":
                assert config.py_version == f"py{py_version}"
        else:
            # Should raise ValueError for invalid versions
            try:
                Config(py_version=py_version)
                raise AssertionError(f"Expected ValueError for invalid py_version={py_version}")
            except ValueError as e:
                assert "is not supported" in str(e)
    
    test_py_version_validation()
    print("✓ Config py_version validation test passed")
except Exception as e:
    print(f"✗ Config py_version validation test failed: {e}")
    traceback.print_exc()

# Test 6: parse_args line_length and wrap_length interaction
print("\n[Test 6] Testing parse_args line_length and wrap_length interaction...")
try:
    @given(
        line_length=st.integers(min_value=1, max_value=200),
        wrap_length=st.integers(min_value=0, max_value=300)
    )
    @settings(max_examples=50)
    def test_parse_args_lengths(line_length, wrap_length):
        args = [
            "--line-length", str(line_length),
            "--wrap-length", str(wrap_length)
        ]
        
        result = isort.main.parse_args(args)
        assert result.get("line_length") == line_length
        assert result.get("wrap_length") == wrap_length
        
        # Now test if Config validates the constraint
        if wrap_length > line_length:
            try:
                Config(**result)
                raise AssertionError(f"Expected ValueError for wrap_length={wrap_length} > line_length={line_length}")
            except ValueError:
                pass
        else:
            config = Config(**result)
            assert config.line_length == line_length
            assert config.wrap_length == wrap_length
    
    test_parse_args_lengths()
    print("✓ parse_args line_length and wrap_length interaction test passed")
except Exception as e:
    print(f"✗ parse_args line_length and wrap_length interaction test failed: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test run complete!")