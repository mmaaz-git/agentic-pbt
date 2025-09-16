import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.decoders as decoders

print("="*60)
print("BUG 1: Strip decoder doesn't strip characters")
print("="*60)

# Test Strip with left=1
strip_left = decoders.Strip(left=1)
tokens = ["00000"]
result = strip_left.decode(tokens)
print(f"Strip(left=1).decode(['00000']) = '{result}'")
print(f"Expected: '0000' (first char stripped)")
print(f"Actual:   '{result}'")
print(f"Bug: Strip decoder does not strip characters!\n")

# Test Strip with right=1
strip_right = decoders.Strip(right=1)
result = strip_right.decode(tokens)
print(f"Strip(right=1).decode(['00000']) = '{result}'")
print(f"Expected: '0000' (last char stripped)")
print(f"Actual:   '{result}'")
print(f"Bug confirmed: Strip decoder does not strip characters!\n")

print("="*60)
print("BUG 2: Sequence decoder doesn't apply decoders correctly")
print("="*60)

# Test Sequence with two Strip decoders
decoder1 = decoders.Strip(left=1)
decoder2 = decoders.Strip(right=1)
seq_decoder = decoders.Sequence([decoder1, decoder2])

tokens = ["000"]
result = seq_decoder.decode(tokens)
print(f"Sequence([Strip(left=1), Strip(right=1)]).decode(['000']) = '{result}'")
print(f"Expected: '0' (strip left, then strip right)")
print(f"Actual:   '{result}'")
print(f"Bug: Sequence decoder doesn't apply decoders!\n")

print("="*60)
print("BUG 3: Metaspace decoder behavior")
print("="*60)

# Test Metaspace with single token
metaspace = decoders.Metaspace()
tokens = ["▁0"]
result = metaspace.decode(tokens)
print(f"Metaspace().decode(['▁0']) = '{result}'")
print(f"Expected: ' 0' (▁ replaced with space)")
print(f"Actual:   '{result}'")

# Check if this is the expected behavior
if result == "0":
    print("Note: Metaspace might be trimming leading spaces for single tokens")
    # Test with multiple tokens
    tokens = ["▁hello", "▁world"]
    result = metaspace.decode(tokens)
    print(f"\nMetaspace().decode(['▁hello', '▁world']) = '{result}'")
    print("This might be intended behavior, not a bug.")

print("\n" + "="*60)
print("INVESTIGATION: What does Strip decoder actually do?")
print("="*60)

# Let's test if Strip is for normalizer, not decoder
print("Testing if Strip might be intended for something else...")

# More tests to understand Strip behavior
test_cases = [
    (["hello"], 1, 0),
    (["hello"], 0, 1),
    (["hello"], 2, 0),
    (["a", "b", "c"], 1, 0),
]

for tokens, left, right in test_cases:
    decoder = decoders.Strip(left=left, right=right)
    result = decoder.decode(tokens)
    print(f"Strip(left={left}, right={right}).decode({tokens}) = '{result}'")