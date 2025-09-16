import re
import sys

sys.path.insert(0, '/root/hypothesis-llm/envs/pytest-pretty_env/lib/python3.13/site-packages')
import pytest_pretty

# Common ANSI sequences that might appear in terminal output
common_sequences = [
    # CSI sequences (most common)
    '\x1b[0m',        # Reset
    '\x1b[31m',       # Red
    '\x1b[1m',        # Bold
    '\x1b[2J',        # Clear screen
    '\x1b[H',         # Cursor home
    
    # Other ESC sequences
    '\x1b7',          # Save cursor position (DECSC)
    '\x1b8',          # Restore cursor position (DECRC) 
    '\x1bM',          # Reverse line feed (RI)
    '\x1b=',          # Application keypad mode (DECKPAM)
    '\x1b>',          # Normal keypad mode (DECKPNM)
    '\x1bc',          # Reset terminal (RIS)
    '\x1bD',          # Index/Line feed (IND)
    '\x1bE',          # Next line (NEL)
    
    # Edge cases
    '\x1b',           # Truncated/incomplete sequence
    '\x1b[',          # Incomplete CSI
]

print("Testing real ANSI sequences:")
print("-" * 70)
for seq in common_sequences:
    cleaned = pytest_pretty.ansi_escape.sub('', seq)
    removed = seq != cleaned
    has_esc = '\x1b' in cleaned
    
    # Describe the sequence
    if seq == '\x1b':
        desc = "Lone ESC (truncated sequence)"
    elif seq == '\x1b[':
        desc = "Incomplete CSI sequence"
    elif seq.startswith('\x1b['):
        desc = f"CSI sequence"
    else:
        desc = f"ESC sequence"
    
    print(f"Sequence: {repr(seq):15} | {desc:30} | Removed: {'Yes' if removed else 'NO'}")
    if not removed and '\x1b' in seq:
        print(f"  WARNING: ESC character not removed!")

print("\n" + "=" * 70)
print("IMPACT ASSESSMENT:")
print("-" * 70)
print("The regex fails to remove several legitimate ANSI sequences:")
print("1. Single-character ESC sequences (ESC M, ESC D, ESC E, etc.)")
print("   These are real ANSI sequences used for terminal control")
print("2. Truncated/incomplete sequences (lone ESC, ESC[)")
print("   These could appear if output is truncated or buffered incorrectly")
print()
print("This could cause parseoutcomes to fail if terminal output contains")
print("these sequences, leading to incorrect parsing of test results.")
print()
print("Severity: MEDIUM - These sequences are less common but could appear")
print("in real terminal output, especially with certain terminal emulators")
print("or when output is truncated/buffered.")