"""Minimal reproductions of discovered bugs in isort.place"""
from mock_deps import Config
import place


def reproduce_bug1_empty_module_name():
    """Bug 1: Empty module name doesn't return default section."""
    print("Bug 1: Empty module name handling")
    print("-" * 40)
    
    config = Config(default_section="THIRDPARTY")
    result = place.module("", config)
    
    print(f"Config default_section: {config.default_section}")
    print(f"Result for empty module name: {result}")
    print(f"Expected: {config.default_section}")
    print(f"Bug: Returns {result} instead of {config.default_section}")
    
    # Investigation: Let's trace through the logic
    print("\nTracing through module_with_reason(''):")
    result_with_reason = place.module_with_reason("", config)
    print(f"Result: {result_with_reason}")
    
    # Check each function
    print("\nChecking individual functions:")
    print(f"_forced_separate('', config): {place._forced_separate('', config)}")
    print(f"_local('', config): {place._local('', config)}")
    print(f"_known_pattern('', config): {place._known_pattern('', config)}")
    print(f"_src_path('', config): {place._src_path('', config)}")
    
    return result != config.default_section  # Returns True if bug exists


def reproduce_bug2_dot_prefix_priority():
    """Bug 2: Modules starting with '.' still match forced_separate patterns."""
    print("\n\nBug 2: Dot prefix priority")
    print("-" * 40)
    
    module_name = ".relative"
    pattern = "relative*"
    
    config = Config(forced_separate=[pattern])
    result = place.module(module_name, config)
    
    print(f"Module name: {module_name}")
    print(f"Forced separate pattern: {pattern}")
    print(f"Result: {result}")
    print(f"Expected: LOCALFOLDER (because it starts with '.')")
    print(f"Bug: Returns {result} instead of LOCALFOLDER")
    
    # The issue is in module_with_reason - it checks forced_separate before _local
    print("\nOrder of checks in module_with_reason:")
    print("1. _forced_separate (should be after _local)")
    print("2. _local")
    print("3. _known_pattern")
    print("4. _src_path")
    
    return result != "LOCALFOLDER"  # Returns True if bug exists


def reproduce_bug3_none_config():
    """Bug 3: Passing None as config causes AttributeError."""
    print("\n\nBug 3: None config handling")
    print("-" * 40)
    
    try:
        result = place.module("test.module", None)
        print(f"Result with None config: {result}")
        print("Bug: Should use DEFAULT_CONFIG but doesn't handle None properly")
        return False
    except AttributeError as e:
        print(f"Error when passing None config: {e}")
        print("Bug: AttributeError instead of using DEFAULT_CONFIG")
        return True  # Returns True if bug exists


if __name__ == "__main__":
    print("Reproducing bugs found in isort.place module")
    print("=" * 50)
    
    bugs_found = []
    
    if reproduce_bug1_empty_module_name():
        bugs_found.append("Bug 1: Empty module name handling")
    
    if reproduce_bug2_dot_prefix_priority():
        bugs_found.append("Bug 2: Dot prefix priority")
        
    if reproduce_bug3_none_config():
        bugs_found.append("Bug 3: None config handling")
    
    print("\n" + "=" * 50)
    print(f"Total bugs found: {len(bugs_found)}")
    for bug in bugs_found:
        print(f"  - {bug}")