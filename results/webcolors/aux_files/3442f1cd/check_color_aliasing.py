"""Check if the aqua/cyan aliasing is expected behavior."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/webcolors_env/lib/python3.13/site-packages')

import webcolors

print("Checking aqua/cyan aliasing:")
print(f"aqua -> hex: {webcolors.name_to_hex('aqua')}")
print(f"cyan -> hex: {webcolors.name_to_hex('cyan')}")

hex_value = webcolors.name_to_hex('aqua')
print(f"\n#00ffff -> name: {webcolors.hex_to_name('#00ffff')}")

print("\nThis appears to be expected behavior - aqua and cyan are aliases")
print("for the same color (#00ffff) in CSS, and hex_to_name returns")
print("one canonical name. This is not a bug.")