import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

import isort.wrap_modes as wrap_modes

# Test with various integers
test_values = [0, 5, 10, 11, 12, 13, 100]

for value in test_values:
    try:
        mode = wrap_modes.from_string(str(value))
        print(f"from_string('{value}'): {mode} (value={mode.value})")
    except ValueError as e:
        print(f"from_string('{value}'): ValueError - {e}")
    except Exception as e:
        print(f"from_string('{value}'): {type(e).__name__} - {e}")

# Check how many wrap modes exist
print(f"\nTotal wrap modes: {len(wrap_modes._wrap_modes)}")
print(f"Wrap mode names: {list(wrap_modes._wrap_modes.keys())}")