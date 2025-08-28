"""Investigate the rdoc() randomness issue"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/beautifulsoup4_env/lib/python3.13/site-packages')

import bs4.diagnose as diagnose
import random

# Test multiple times to see the pattern
print("Testing rdoc(1) with different random seeds:")
for seed in range(100):
    random.seed(seed)
    result = diagnose.rdoc(1)
    content = result[6:-7]  # Skip '<html>' and '</html>'
    if len(content) == 0:
        print(f"Seed {seed}: EMPTY content! Full result: {repr(result)}")

# Let's find what choices lead to empty content
print("\n\nAnalyzing what choice values create content:")
for choice_val in range(4):
    print(f"\nChoice {choice_val}:")
    if choice_val == 0:
        print("  Creates opening tag like <p>")
    elif choice_val == 1:
        print("  Creates a sentence")
    elif choice_val == 2:
        print("  Creates closing tag like </p>")
    else:
        print("  Does nothing (no element added)")

# Now let's understand the actual implementation
print("\n\nLooking at rdoc implementation (lines 202-212):")
print("""
for i in range(num_elements):
    choice = random.randint(0, 3)
    if choice == 0:
        # New tag.
        tag_name = random.choice(tag_names)
        elements.append("<%s>" % tag_name)
    elif choice == 1:
        elements.append(rsentence(random.randint(1, 4)))
    elif choice == 2:
        # Close a tag.
        tag_name = random.choice(tag_names)
        elements.append("</%s>" % tag_name)
    # NOTE: No else clause! When choice==3, nothing happens!
""")

# Count how many times we get empty content
empty_count = 0
total_tests = 1000
for seed in range(total_tests):
    random.seed(seed)
    result = diagnose.rdoc(1)
    content = result[6:-7]
    if len(content) == 0:
        empty_count += 1

print(f"\nOut of {total_tests} tests with rdoc(1):")
print(f"  Empty content: {empty_count} times ({empty_count/total_tests*100:.1f}%)")
print(f"  Non-empty content: {total_tests - empty_count} times ({(total_tests - empty_count)/total_tests*100:.1f}%)")