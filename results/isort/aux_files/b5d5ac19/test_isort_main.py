"""Property-based tests for isort.main module"""

import sys
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
from io import StringIO
from typing import Dict, Any, List

import isort.main
from isort.settings import Config
from isort.wrap_modes import WrapModes


# Test 1: Config wrap_length constraint
@given(
    line_length=st.integers(min_value=1, max_value=1000),
    wrap_length=st.integers(min_value=0, max_value=2000)
)
def test_config_wrap_length_constraint(line_length, wrap_length):
    """Test that Config enforces wrap_length <= line_length constraint"""
    config_dict = {
        "line_length": line_length,
        "wrap_length": wrap_length
    }
    
    if wrap_length > line_length:
        # Should raise ValueError when wrap_length > line_length
        with pytest.raises(ValueError, match="wrap_length must be set lower than or equal to line_length"):
            Config(**config_dict)
    else:
        # Should succeed when wrap_length <= line_length
        config = Config(**config_dict)
        assert config.wrap_length == wrap_length
        assert config.line_length == line_length


# Test 2: parse_args handles mutually exclusive flags
@given(
    include_float_to_top=st.booleans(),
    include_dont_float_to_top=st.booleans()
)
def test_parse_args_mutually_exclusive_flags(include_float_to_top, include_dont_float_to_top):
    """Test that parse_args handles mutually exclusive float-to-top flags correctly"""
    args = []
    
    if include_float_to_top:
        args.append("--float-to-top")
    if include_dont_float_to_top:
        args.append("--dont-float-to-top")
    
    if include_float_to_top and include_dont_float_to_top:
        # Should exit when both flags are set
        with pytest.raises(SystemExit):
            isort.main.parse_args(args)
    else:
        # Should succeed otherwise
        result = isort.main.parse_args(args)
        if include_dont_float_to_top:
            assert result.get("float_to_top") == False
        elif include_float_to_top:
            assert result.get("float_to_top") == True


# Test 3: multi_line_output parsing
@composite
def multi_line_output_value(draw):
    """Generate valid multi_line_output values"""
    # WrapModes has values 0-10 based on the wrap functions
    mode = draw(st.sampled_from([
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "GRID", "VERTICAL", "HANGING_INDENT", "VERTICAL_HANGING_INDENT",
        "VERTICAL_GRID", "VERTICAL_GRID_GROUPED", "VERTICAL_GRID_GROUPED_NO_COMMA",
        "NOQA", "VERTICAL_HANGING_INDENT_BRACKET", "VERTICAL_PREFIX_FROM_MODULE_IMPORT",
        "HANGING_INDENT_WITH_PARENTHESES", "BACKSLASH_GRID"
    ]))
    return mode


@given(multi_line_mode=multi_line_output_value())
def test_parse_args_multi_line_output(multi_line_mode):
    """Test that parse_args correctly handles multi_line_output values"""
    args = ["--multi-line", multi_line_mode]
    
    try:
        result = isort.main.parse_args(args)
        # Should have converted to WrapModes enum
        assert "multi_line_output" in result
        assert isinstance(result["multi_line_output"], WrapModes)
    except (ValueError, KeyError):
        # Invalid mode names should fail
        pass


# Test 4: _preconvert function
@given(
    value=st.one_of(
        st.sets(st.text()),
        st.frozensets(st.integers()),
        st.text(),
        st.integers(),
        st.booleans(),
        st.none(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_preconvert_function(value):
    """Test that _preconvert handles various types correctly"""
    try:
        result = isort.main._preconvert(value)
        
        if isinstance(value, (set, frozenset)):
            # Sets should convert to lists
            assert isinstance(result, list)
            assert set(result) == set(value)
        elif isinstance(value, WrapModes):
            # WrapModes should convert to name string
            assert isinstance(result, str)
        else:
            # Other unhandled types should raise TypeError
            pass
    except TypeError as e:
        # Should only raise TypeError for unserializable objects
        assert "Unserializable object" in str(e)
        # Basic types should not raise
        assert not isinstance(value, (str, int, bool, type(None)))


# Test 5: parse_args handles various valid argument combinations
@given(
    check=st.booleans(),
    diff=st.booleans(),
    verbose=st.booleans(),
    quiet=st.booleans(),
    atomic=st.booleans(),
    line_length=st.integers(min_value=1, max_value=200),
    jobs=st.one_of(st.none(), st.integers(min_value=-10, max_value=10)),
    profile=st.sampled_from(["", "black", "django", "google", "pycharm"])
)
def test_parse_args_combinations(check, diff, verbose, quiet, atomic, line_length, jobs, profile):
    """Test that parse_args handles various valid argument combinations without crashing"""
    args = []
    
    if check:
        args.append("--check")
    if diff:
        args.append("--diff")
    if verbose:
        args.append("--verbose")
    if quiet:
        args.append("--quiet")
    if atomic:
        args.append("--atomic")
    
    args.extend(["--line-length", str(line_length)])
    
    if jobs is not None:
        args.extend(["--jobs", str(jobs)])
    
    if profile:
        args.extend(["--profile", profile])
    
    # Should not crash for any valid combination
    result = isort.main.parse_args(args)
    assert isinstance(result, dict)
    
    if check:
        assert result.get("check") == True
    if diff:
        assert result.get("show_diff") == True
    if verbose:
        assert result.get("verbose") == True
    if quiet:
        assert result.get("quiet") == True
    if atomic:
        assert result.get("atomic") == True
    assert result.get("line_length") == line_length
    if jobs is not None:
        assert result.get("jobs") == jobs
    if profile:
        assert result.get("profile") == profile


# Test 6: Deprecated single dash arguments are remapped
@given(deprecated_arg=st.sampled_from(["-ac", "-af", "-ca", "-cs", "-df", "-ds", "-dt", 
                                        "-fas", "-fass", "-ff", "-fgw", "-fss"]))
def test_deprecated_args_remapping(deprecated_arg):
    """Test that deprecated single dash arguments are properly remapped"""
    args = [deprecated_arg]
    
    # Should not crash and should remap the argument
    result = isort.main.parse_args(args)
    assert isinstance(result, dict)
    
    # Check that remapped_deprecated_args is recorded
    if "remapped_deprecated_args" in result:
        assert deprecated_arg in result["remapped_deprecated_args"]


# Test 7: sort_imports function error handling
@given(
    file_name=st.text(min_size=1),
    check=st.booleans(),
    ask_to_apply=st.booleans(),
    write_to_stdout=st.booleans()
)
def test_sort_imports_error_handling(file_name, check, ask_to_apply, write_to_stdout):
    """Test that sort_imports handles various inputs without crashing unexpectedly"""
    config = Config()
    
    # Since file doesn't exist, this should return None (OSError) or handle gracefully
    result = isort.main.sort_imports(
        file_name=file_name,
        config=config,
        check=check,
        ask_to_apply=ask_to_apply,
        write_to_stdout=write_to_stdout
    )
    
    # Should either return None (for file not found) or a SortAttempt
    assert result is None or isinstance(result, isort.main.SortAttempt)


# Test 8: Config with contradictory settings
@given(
    force_alphabetical_sort=st.booleans(),
    no_sections=st.booleans(),
    force_alphabetical_sort_within_sections=st.booleans()
)
def test_config_force_alphabetical_interactions(force_alphabetical_sort, no_sections, 
                                               force_alphabetical_sort_within_sections):
    """Test Config handles force_alphabetical_sort implications correctly"""
    config = Config(
        force_alphabetical_sort=force_alphabetical_sort,
        no_sections=no_sections,
        force_alphabetical_sort_within_sections=force_alphabetical_sort_within_sections
    )
    
    if force_alphabetical_sort:
        # When force_alphabetical_sort is True, it should set these
        assert config.force_alphabetical_sort_within_sections == True
        assert config.no_sections == True
        assert config.lines_between_types == 1
        assert config.from_first == True
    else:
        # Otherwise, should preserve original values
        assert config.no_sections == no_sections
        assert config.force_alphabetical_sort_within_sections == force_alphabetical_sort_within_sections


if __name__ == "__main__":
    pytest.main([__file__, "-v"])