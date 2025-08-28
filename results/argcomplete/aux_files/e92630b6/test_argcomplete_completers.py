import argcomplete.completers
from hypothesis import given, strategies as st, settings


# Property 1: ChoicesCompleter._convert always returns a string
@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.text(),
    st.binary(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.tuples(st.integers(), st.text())
))
def test_choices_completer_convert_always_returns_string(choice):
    completer = argcomplete.completers.ChoicesCompleter([])
    result = completer._convert(choice)
    assert isinstance(result, str), f"_convert({choice!r}) returned {type(result).__name__}, not str"


# Property 2: ChoicesCompleter preserves number of choices
@given(st.lists(st.one_of(
    st.none(),
    st.booleans(), 
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
)))
def test_choices_completer_preserves_count(choices):
    completer = argcomplete.completers.ChoicesCompleter(choices)
    result = list(completer())
    assert len(result) == len(choices), f"Expected {len(choices)} results, got {len(result)}"
    # Also verify all are strings
    assert all(isinstance(r, str) for r in result), "Not all results are strings"


# Property 3: FilesCompleter.allowednames strips "*" and "." prefixes correctly
@given(st.lists(st.text()))
def test_files_completer_strips_prefixes(names):
    completer = argcomplete.completers.FilesCompleter(names)
    for i, processed in enumerate(completer.allowednames):
        original = names[i]
        # Verify the stripping logic
        expected = original.lstrip("*").lstrip(".")
        assert processed == expected, f"Expected '{expected}' from '{original}', got '{processed}'"


# Property 4: FilesCompleter string-to-list conversion
@given(st.one_of(st.text(), st.binary()))
def test_files_completer_string_to_list_conversion(name):
    completer = argcomplete.completers.FilesCompleter(name)
    # Should convert string/bytes to list
    assert isinstance(completer.allowednames, list), f"allowednames should be list, got {type(completer.allowednames)}"
    assert len(completer.allowednames) == 1, f"Single string should become single-element list, got {len(completer.allowednames)}"
    # Should have stripped prefixes
    if isinstance(name, bytes):
        expected = name.lstrip(b"*").lstrip(b".").decode('utf-8', errors='replace')
    else:
        expected = name.lstrip("*").lstrip(".")
    assert completer.allowednames[0] == expected


# Property 5: Test combinations of prefix stripping
@given(st.text())
def test_files_completer_prefix_stripping_combinations(text):
    # Test various prefix combinations
    test_cases = [
        text,
        "*" + text,
        "." + text,
        "*." + text,
        "**" + text,
        ".." + text,
        "***..." + text
    ]
    
    for test_input in test_cases:
        completer = argcomplete.completers.FilesCompleter([test_input])
        result = completer.allowednames[0]
        # The documented behavior is lstrip("*").lstrip(".")
        expected = test_input.lstrip("*").lstrip(".")
        assert result == expected, f"Input '{test_input}' should become '{expected}', got '{result}'"


# Property 6: SuppressCompleter.suppress always returns True  
@given(st.data())
def test_suppress_completer_always_returns_true(data):
    completer = argcomplete.completers.SuppressCompleter()
    # The suppress method takes no arguments and always returns True
    result = completer.suppress()
    assert result is True, f"suppress() should always return True, got {result}"


# Property 7: DirectoriesCompleter initialization
def test_directories_completer_initialization():
    # DirectoriesCompleter should properly initialize with os.path.isdir predicate
    completer = argcomplete.completers.DirectoriesCompleter()
    assert hasattr(completer, 'predicate'), "DirectoriesCompleter should have a predicate attribute"
    import os
    assert completer.predicate == os.path.isdir, "DirectoriesCompleter predicate should be os.path.isdir"