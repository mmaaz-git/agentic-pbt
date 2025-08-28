import re
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import isort.stdlibs as stdlibs

# Property 1: Union correctness - all.stdlib should equal py2 | py3
def test_all_stdlib_union():
    computed_all = stdlibs.py2.stdlib | stdlibs.py3.stdlib
    assert stdlibs.all.stdlib == computed_all, f"all.stdlib does not equal py2 | py3 union"

# Property 2: py3 union correctness
def test_py3_stdlib_union():
    computed_py3 = (
        stdlibs.py36.stdlib
        | stdlibs.py37.stdlib
        | stdlibs.py38.stdlib
        | stdlibs.py39.stdlib
        | stdlibs.py310.stdlib
        | stdlibs.py311.stdlib
        | stdlibs.py312.stdlib
        | stdlibs.py313.stdlib
    )
    assert stdlibs.py3.stdlib == computed_py3, f"py3.stdlib does not equal union of all py3x versions"

# Property 3: Valid module names - all entries should be valid Python module/package names
# According to Python docs, module names must be valid identifiers
VALID_MODULE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

@given(st.sampled_from([
    stdlibs.py2, stdlibs.py3, stdlibs.py27, stdlibs.py36, stdlibs.py37,
    stdlibs.py38, stdlibs.py39, stdlibs.py310, stdlibs.py311, stdlibs.py312, stdlibs.py313
]))
def test_valid_module_names(version_module):
    for module_name in version_module.stdlib:
        assert isinstance(module_name, str), f"{module_name} is not a string"
        assert VALID_MODULE_NAME_PATTERN.match(module_name), f"{module_name} is not a valid module name"

# Property 4: Non-empty sets
def test_non_empty_stdlibs():
    versions = [
        stdlibs.py2, stdlibs.py3, stdlibs.py27, stdlibs.py36, stdlibs.py37,
        stdlibs.py38, stdlibs.py39, stdlibs.py310, stdlibs.py311, stdlibs.py312, stdlibs.py313
    ]
    for version_module in versions:
        assert len(version_module.stdlib) > 0, f"{version_module.__name__} has empty stdlib"

# Property 5: Type invariant - all entries are strings
@given(st.sampled_from([
    stdlibs.py2, stdlibs.py3, stdlibs.py27, stdlibs.py36, stdlibs.py37,
    stdlibs.py38, stdlibs.py39, stdlibs.py310, stdlibs.py311, stdlibs.py312, stdlibs.py313, stdlibs.all
]))
def test_all_entries_are_strings(version_module):
    for entry in version_module.stdlib:
        assert isinstance(entry, str), f"Entry {entry} in {version_module.__name__} is not a string but {type(entry)}"

# Property 6: Python 2 should contain py27 modules
def test_py2_contains_py27():
    assert stdlibs.py27.stdlib.issubset(stdlibs.py2.stdlib), "py27 modules not subset of py2"

# Property 7: Common core modules should be present in all Python versions
# These are fundamental modules that have existed in all Python versions
CORE_MODULES = {'sys', 'os', 'math', 'time', 're', 'json', 'collections'}

def test_core_modules_present():
    for module_name in CORE_MODULES:
        assert module_name in stdlibs.py2.stdlib, f"{module_name} not in py2 stdlib"
        assert module_name in stdlibs.py3.stdlib, f"{module_name} not in py3 stdlib"
        # Check all py3 versions
        for version in [stdlibs.py36, stdlibs.py37, stdlibs.py38, stdlibs.py39, 
                       stdlibs.py310, stdlibs.py311, stdlibs.py312, stdlibs.py313]:
            assert module_name in version.stdlib, f"{module_name} not in {version.__name__} stdlib"

# Property 8: No stdlib set should be identical to another (each version has some differences)
def test_version_uniqueness():
    all_versions = [
        (stdlibs.py27, "py27"),
        (stdlibs.py36, "py36"),
        (stdlibs.py37, "py37"),
        (stdlibs.py38, "py38"),
        (stdlibs.py39, "py39"),
        (stdlibs.py310, "py310"),
        (stdlibs.py311, "py311"),
        (stdlibs.py312, "py312"),
        (stdlibs.py313, "py313"),
    ]
    
    for i, (v1, n1) in enumerate(all_versions):
        for v2, n2 in all_versions[i+1:]:
            # While sets might be very similar, they shouldn't be identical
            # Each Python version adds or removes some modules
            assert v1.stdlib != v2.stdlib, f"{n1} and {n2} have identical stdlib sets"

# Property 9: Module names should not contain invalid characters
@given(st.sampled_from([
    stdlibs.py2, stdlibs.py3, stdlibs.py27, stdlibs.py36, stdlibs.py37,
    stdlibs.py38, stdlibs.py39, stdlibs.py310, stdlibs.py311, stdlibs.py312, stdlibs.py313, stdlibs.all
]))
def test_no_invalid_characters(version_module):
    for module_name in version_module.stdlib:
        # Module names shouldn't contain dots (that would be submodules)
        assert '.' not in module_name, f"Module name {module_name} contains dot"
        # Module names shouldn't contain spaces
        assert ' ' not in module_name, f"Module name {module_name} contains space"
        # Module names shouldn't contain hyphens
        assert '-' not in module_name, f"Module name {module_name} contains hyphen"