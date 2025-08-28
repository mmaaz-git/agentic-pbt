import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.decoders as decoders

# Test basic decoder behavior
test_tokens = ["Hello", "▁world", "##ing", "<0x61>", "▁", "</w>"]

print("Testing decoder behavior with tokens:", test_tokens)
print()

# Test each decoder
decoders_to_test = [
    ("BPEDecoder", decoders.BPEDecoder()),
    ("ByteFallback", decoders.ByteFallback()),
    ("ByteLevel", decoders.ByteLevel()),
    ("Metaspace", decoders.Metaspace()),
    ("WordPiece", decoders.WordPiece()),
    ("Fuse", decoders.Fuse()),
    ("Strip (left=1)", decoders.Strip(left=1)),
    ("Strip (right=1)", decoders.Strip(right=1)),
    ("CTC", decoders.CTC()),
]

for name, decoder in decoders_to_test:
    try:
        result = decoder.decode(test_tokens)
        print(f"{name:20} => '{result}'")
    except Exception as e:
        print(f"{name:20} => ERROR: {e}")

# Test Sequence decoder
print("\nTesting Sequence decoder (BPE + Metaspace):")
seq = decoders.Sequence([decoders.BPEDecoder(), decoders.Metaspace()])
try:
    result = seq.decode(test_tokens)
    print(f"  Result: '{result}'")
except Exception as e:
    print(f"  ERROR: {e}")

# Test Replace decoder with pattern
print("\nTesting Replace decoder:")
rep = decoders.Replace("_", " ")
test_replace = ["Hello_world", "_test_", "__double__"]
try:
    result = rep.decode(test_replace)
    print(f"  Input:  {test_replace}")
    print(f"  Result: '{result}'")
except Exception as e:
    print(f"  ERROR: {e}")